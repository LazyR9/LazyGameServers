import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Button, Form, InputGroup } from "react-bootstrap";
import { useFetchQuery } from "../querys";
import { useQueryClient } from "@tanstack/react-query";

export default function ServerConsole({ type, serverId }) {
  const [enteredCmd, setEnteredCmd] = useState("");

  const apiEndpoint = `/api/servers/${encodeURIComponent(type)}/${serverId}/console`

  const queryKey = useMemo(() => ["servers", type, serverId, "console"], [type, serverId]);

  const { isPending, data: serverConsole } = useFetchQuery({
    queryKey,
    apiEndpoint,
  });

  const queryClient = useQueryClient();

  useEffect(() => {
    const eventSource = new EventSource(apiEndpoint + "/stream");
    eventSource.addEventListener("message", (event) => {
      queryClient.setQueryData(queryKey, (data) => ({
        lines: [
          ...data.lines,
          JSON.parse(event.data)
        ]
      }));
    })
    return () => eventSource.close();
  }, [apiEndpoint, queryKey, queryClient]);

  const ref = useRef();

  useLayoutEffect(() => {
    if (ref.current)// && ref.current.scrollTop === ref.current.scrollHeight - ref.current.clientHeight)
      ref.current.scrollTop = ref.current.scrollHeight;
  }, [ref, serverConsole]);

  return (
    <div className="console-wrapper">
      <div className="console rounded-top" ref={ref}>
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