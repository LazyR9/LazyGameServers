import { useParams, useNavigate } from "react-router-dom";
import { Badge, Button, ButtonGroup, OverlayTrigger, Placeholder, Tab, Tabs, Tooltip } from "react-bootstrap";
import ErrorPage, { ResponseError } from "../errors";
import ServerConsole from "../components/Console";
import { useServerQuery } from "../querys";
import { useEffect, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ServerSettings from "../components/Settings";
import ServerFileBrowser from "../components/FileBrowser";
import { getServerEndpoint } from "../utils";

// TODO organize imports in all files

export function ServerIndicator({ server, className }) {
  return (
    <OverlayTrigger placement="right" overlay={<Tooltip>{server.status.value.slice(0, 1) + server.status.value.slice(1).toLowerCase()}</Tooltip>}>
      <span className={"indicator " + server.status.value.toLowerCase() + (className ? (" " + className) : '')} />
    </OverlayTrigger>
  );
}

export function ServerControls({ server, children, ...props }) {
  const apiEndpoint = getServerEndpoint(server.game.value, server.id.value);
  let start = "Start";
  let stop = "Stop";
  if (children) {
    if (children instanceof Array && children.length === 2) {
      start = children[0];
      stop = children[1];
    } else {
      console.warn("ServerControls got incorrect children!\nPlease provide two seperate elements to be wrapped in the start than stop button.");
    }
  }
  return (
    <ButtonGroup>
      <Button disabled={server.status.value !== "STOPPED"} onClick={() => fetch(apiEndpoint + "/start")} {...props}>{start}</Button>
      <Button disabled={server.status.value !== "RUNNING"} onClick={() => fetch(apiEndpoint + "/stop")} {...props}>{stop}</Button>
    </ButtonGroup>
  );
}

export default function Server() {
  const { type, serverId, tab } = useParams();
  const navigate = useNavigate();

  const { isPending, isError, data: server, error } = useServerQuery({ type, serverId });

  const queryClient = useQueryClient();
  const apiEndpoint = getServerEndpoint(type, serverId);
  const queryKey = useMemo(() => ["servers", type, serverId], [type, serverId]);
  useEffect(() => {
    const eventSource = new EventSource(apiEndpoint + "/stream");

    eventSource.addEventListener("console_line", (event) => {
      queryClient.setQueryData([...queryKey, "console"], (data) => ({
        ...data,
        lines: [
          ...(data?.lines ?? []),
          JSON.parse(event.data),
        ]
      }));
    });

    eventSource.addEventListener("status", (event) => {
      queryClient.setQueryData(queryKey, (data) => ({
        ...data,
        status: {
          ...data.status,
          value: JSON.parse(event.data).status,
        }
      }));
    });

    eventSource.addEventListener("console_clear", (event) => {
      queryClient.setQueryData([...queryKey, "console"], (data) => ({
        ...data,
        lines: [],
      }));
    });

    return () => eventSource.close();
  }, [apiEndpoint, queryKey, queryClient]);

  if (isError) {
    if (error instanceof ResponseError && error.response.status === 404) {
      return <ErrorPage title="Server not Found!" subtitle={<>Server <code>{type}/{serverId}</code> doesn't exist!</>} />;
    }
    return <ErrorPage message={error.message} />
  }

  return (
    <div id="server">
      {/* TODO make the pending page resemble the actual page */}
      {isPending ? (
        <>
          <Placeholder as='h1' animation="glow">
            <Placeholder xs={6} />
          </Placeholder>
          <Placeholder as='h4' animation="glow">
            <Placeholder xs={6} />
          </Placeholder>
        </>
      ) : (
        <>
          <div className="pb-2 position-relative">
            <span className="h1 pe-2">{server.id.value}</span>
            <Badge bg="secondary">
              <span className="h4">{server.game.value}</span>
            </Badge>
            <ServerIndicator className="ms-2" server={server} />
          </div>

          <ServerControls server={server} />

          <Tabs
            id="server-tabs"
            className="mt-2"
            mountOnEnter
            // TODO having the tabs controlled by routers like this causes extra renders
            // should probably fix that at some point but it isn't a problem right now so i'll ignore it
            activeKey={tab}
            onSelect={(nextTab) => navigate(`${tab !== undefined ? '../' : ''}${nextTab}`, { relative: "path", replace: true })}
          >
            <Tab eventKey="console" title="Console">
              <ServerConsole />
            </Tab>
            <Tab eventKey="files" title="Files">
              <ServerFileBrowser />
            </Tab>
            <Tab eventKey="settings" title="Settings">
              <ServerSettings />
            </Tab>
          </Tabs>
        </>
      )}
    </div>
  );
}