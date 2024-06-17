import { Form, InputGroup } from "react-bootstrap";
import { useServerQuery } from "../querys"
import { useParams } from "react-router-dom";

export default function ServerSettings() {
  const { type, serverId } = useParams();
  const { data: server } = useServerQuery({ type, serverId });

  return (<>
    {/* TODO this */}
    <p>NOTE: these are read only for now, I need to refactor somethings to make settings easier</p>
    <Form>
      {Object.keys(server).map(key => {
        const value = server[key];
        if (typeof(value) === "object" || key === "status")
          return null;
        return (
          <InputGroup className="mb-3">
            <InputGroup.Text>{key}</InputGroup.Text>
            <Form.Control type="text" defaultValue={value} />
          </InputGroup>
        );
      })}
    </Form>
  </>)
}