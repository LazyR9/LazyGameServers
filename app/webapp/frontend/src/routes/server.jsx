import { Form } from "react-router-dom";

export default function Server() {
  const server = {
    game: "minecraft",
    id: "server1",
    // start cmd, stop cmd, etc
  };

  return (
    <div id="server">
      <div>
        <h1>{server.id}</h1>

        <div>
          <Form action="edit">
            <button type="submit">Edit</button>
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
            <button type="submit">Delete</button>
          </Form>
        </div>
      </div>
    </div>
  );
}