import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { Button, Form, InputGroup } from "react-bootstrap";
import { useFetchQuery } from "../querys";
import { getServerEndpoint } from "../utils";
import { useParams } from "react-router-dom";

export default function ServerConsole() {
  const { type, serverId } = useParams();

  const [enteredCmd, setEnteredCmd] = useState("");

  const apiEndpoint = getServerEndpoint(type, serverId) + "/console";

  const queryKey = useMemo(() => ["servers", type, serverId, "console"], [type, serverId]);

  const { isSuccess, data: serverConsole } = useFetchQuery({
    queryKey,
    apiEndpoint,
  });

  const ref = useRef();

  useLayoutEffect(() => {
    if (ref.current)// && ref.current.scrollTop === ref.current.scrollHeight - ref.current.clientHeight)
      ref.current.scrollTop = ref.current.scrollHeight;
  }, [ref, serverConsole]);

  return (
    <div className="console-wrapper">
      <div className="console rounded-top" ref={ref}>
        {isSuccess && serverConsole.lines.map((value, index) => (
          // TODO actually color lines instead of just stripping color
          <div key={index} className={value.error ? "console-line-error" : undefined}>{value.line.replace(/\033\[(.*?)m/g, "")}</div>
        ))}
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