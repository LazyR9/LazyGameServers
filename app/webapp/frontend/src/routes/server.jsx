import { useParams } from "react-router-dom";
import { Badge, Button, ButtonGroup, OverlayTrigger, Placeholder, Tab, Tabs, Tooltip } from "react-bootstrap";
import ErrorPage, { ResponseError } from "../errors";
import ServerConsole from "../components/Console";
import { useServerQuery } from "../querys";
import { useEffect, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ServerSettings from "../components/Settings";

export default function Server() {
  const { type, serverId } = useParams();
  
  const { isPending, isError, data: server, error } = useServerQuery({ type, serverId });
  
  const queryClient = useQueryClient();
  const apiEndpoint = `/api/servers/${encodeURIComponent(type)}/${serverId}`;
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
        status: JSON.parse(event.data).status,
      }))
    })
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
            <span className="h1 pe-2">{server.id}</span>
            <Badge bg="secondary">
              <span className="h4">{server.game}</span>
            </Badge>
            <OverlayTrigger placement="right" overlay={<Tooltip>{server.status.slice(0, 1) + server.status.slice(1).toLowerCase()}</Tooltip>}>
              <span className={"indicator " + server.status.toLowerCase()} />
            </OverlayTrigger>
          </div>

          <ButtonGroup>
            <Button disabled={server.status !== "STOPPED"} onClick={() => fetch(apiEndpoint + "/start")}>Start</Button>
            <Button disabled={server.status !== "RUNNING"} onClick={() => fetch(apiEndpoint + "/stop")}>Stop</Button>
          </ButtonGroup>

          <Tabs
            id="server-tabs"
            className="mt-2"
          >
            <Tab eventKey="console" title="Console">
              <ServerConsole type={type} serverId={serverId} />
            </Tab>
            <Tab eventKey="settings" title="Setttings">
              <ServerSettings type={type} serverId={serverId} />
            </Tab>
          </Tabs>
        </>
      )}
    </div>
  );
}