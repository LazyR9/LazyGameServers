import { useParams } from "react-router-dom";
import { Badge, Button, ButtonGroup, Form, OverlayTrigger, Placeholder, Tab, Tabs, Tooltip } from "react-bootstrap";
import ErrorPage, { ResponseError } from "../errors";
import ServerConsole from "../components/Console";
import { useFetchQuery } from "../querys";

export default function Server() {
  const { type, serverId } = useParams();
  const apiEndpoint = `/api/servers/${encodeURIComponent(type)}/${serverId}`;

  const { isPending, isError, data: server, error } = useFetchQuery({queryKey: ["servers", type, serverId], apiEndpoint});

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
              Pretend there are some settings here
            </Tab>
          </Tabs>

          {/* TODO figure out these, they're copied from a tutorial iirc */}
          <br /><br /><br /><br />
          <div className="mt-4">
            <Form action="edit">
              <Button type="submit">Edit</Button>
            </Form>
            <Form
              method="post"
              action="destroy"
              onSubmit={(event) => {
                // eslint-disable-next-line no-restricted-globals
                if (!confirm("confirm pls thx")) {
                  event.preventDefault();
                }
              }}
            >
              <Button type="submit">Delete</Button>
            </Form>
          </div>
        </>
      )}
    </div>
  );
}