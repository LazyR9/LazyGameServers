import { useState } from "react";
import { Button, Form, InputGroup } from "react-bootstrap";
import { useFetchQuery } from "../querys";

export default function ServerConsole({ type, serverId }) {
  //const [lines, setLines] = useState([]);
  const [enteredCmd, setEnteredCmd] = useState("");

  const apiEndpoint = `/api/servers/${encodeURIComponent(type)}/${serverId}/console`

  const { isPending, data: serverConsole } = useFetchQuery({
    queryKey: ["servers", type, serverId, "console"],
    apiEndpoint,
  });

  return (
    <div className="console-wrapper">
      <div className="console rounded-top">
        {isPending || serverConsole.lines.map((value, index) => (
          <div key={index} className={value.error ? "console-line-error" : undefined}>{value.line}</div>)
        )}
      </div>
      <Form className="list-group-item"
        onSubmit={(event) => {
          event.preventDefault();
          setEnteredCmd("");
          fetch(apiEndpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ command: enteredCmd }),
          });
        }}
      >
        <InputGroup>
          <Form.Control placeholder="Enter console command..." value={enteredCmd} onChange={e => setEnteredCmd(e.target.value)} />
          <Button variant="secondary" type="submit">Send</Button>
        </InputGroup>
      </Form>
    </div>
  );
}