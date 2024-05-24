import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Badge, Button, Form, InputGroup, Placeholder, Tab, Tabs } from "react-bootstrap";
import ErrorPage from "../errors";
import { useState } from "react";

export default function Server() {
  const { type, serverId } = useParams();
  const [lines, setLines] = useState([]);
  const [enteredCmd, setEnteredCmd] = useState("");

  const { isPending, isError, data: server, error } = useQuery({
    queryKey: ["servers", type, serverId],
    queryFn: async () => {
      const response = await fetch(`/api/servers/${encodeURIComponent(type)}/${serverId}`);
      // // TODO only throw error if response failed (otherwise react query will retry 5 times even on 404s)
      // if (!response.ok) {
      //   // TODO the server probably gave us a better error message, show that somehow?
      //   throw new ResponseError(response);
      // }
      return await response.json();
    }
  });

  if (server?.error === '404') {
    return <ErrorPage title="Server not Found!" subtitle={<>Server <code>{type}/{serverId}</code> doesn't exist!</>} />;
  }

  if (isError) {
    return <ErrorPage message={error.message} />
  }

  return (
    <div id="server">
      <div>
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
            <div className="pb-2">
              <span className="h1 pe-2">{server.id}</span>
              <Badge bg="secondary">
                <span className="h4">{server.game}</span>
              </Badge>
            </div>

            <Tabs
              id="server-tabs"
              className="mt-2"
            >
              <Tab eventKey="console" title="Console">
                <div className="console">
                  <div className="console-line-output">This is a line</div>
                  <div className="console-line-error">WWWW WW W WWWW</div>
                  <div className="console-line-output">iiii ii i iiii</div>
                  {lines.map((value) => <div>{value}</div>)}
                </div>
                <Form
                  onSubmit={(event) => {
                    event.preventDefault();
                    setEnteredCmd("");
                    setLines(lines.concat(enteredCmd));
                  }}
                >
                  <Form.Label>Enter console command:</Form.Label>
                  <InputGroup>
                    <Form.Control value={enteredCmd} onChange={e => setEnteredCmd(e.target.value)} />
                    <Button variant="secondary" type="submit">Send</Button>
                  </InputGroup>
                </Form>
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
    </div>
  );
}