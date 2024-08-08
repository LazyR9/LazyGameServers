import { Form } from "react-bootstrap";
import { MutationButton, useFetchMutation, useServerQuery } from "../querys"
import { useParams } from "react-router-dom";
import { getServerEndpoint, makeEnum } from "../utils";
import { useMemo } from "react";

import "./Settings.css";

const data_to_input_map = {
  string: "text",
  int: "number",
}

const Flags = makeEnum([
  "NONE",
  "WRITABLE",
  "SETTINGS",
  "REPLACEMENT",
])

function mapSettings(data, callback) {
  return Object.entries(data).filter(([key, value]) => value.flags & Flags.SETTINGS).map(callback);
}

const data = { "": {} };
function groupSettings(obj, default_group = "") {
  for (const name in obj) {
    const value = obj[name];
    if (!(value.flags & Flags.SETTINGS)) continue;
    if (value.type === "object") {
      groupSettings(value.value, name);
      continue
    }
    const group = value.group || default_group;
    if (!(group in data))
      data[group] = {};
    data[group][name] = value;
  }
}

export default function ServerSettings() {
  const { type, serverId } = useParams();
  const { data: server } = useServerQuery({ type, serverId });

  useMemo(() => groupSettings(server), [server]);

  const mutation = useFetchMutation({ apiEndpoint: getServerEndpoint(type, serverId), auth: true });

  return (
    <Form onSubmit={(e) => {
      e.preventDefault();
      const new_server = {};
      for (const group in data) {
        for (const key in data[group]) {
          new_server[key] = data[group][key].value;
        }
      }
      mutation.mutate(new_server);
    }}>
      {Object.entries(data).map(([key, value]) => (
        <SettingsSection key={key} id={key} name={value.group} data={value} />
      ))}
      <MutationButton mutation={mutation} type="submit" />
    </Form>
  );
}

function SettingsSection({ id, name, data }) {
  return (
    <Form.Group className="settings-section rounded p-3 mb-2">
      <h3>{name || (id && <code className="settings-section-title rounded p-1">{id}</code>) || "Basic Settings"}</h3>
      {mapSettings(data, ([key, value]) => {
        if (value.type in data_to_input_map)
          return (
            <Form.Group key={key} className="mb-3">
              <Form.Label>{value.name || <code>{key}</code>}</Form.Label>
              <Form.Control
                type={data_to_input_map[value.type]}
                defaultValue={value.value}
                disabled={!(value.flags & Flags.WRITABLE)}
                spellCheck={false}
                autoCapitalize="off"
                onChange={e => data[key].value = e.target.value} />
            </Form.Group>
          );
        else if (value.type === 'bool')
          return (
            <Form.Check
              key={key}
              className="mb-3"
              label={value.name || <code>{key}</code>}
              type="switch"
              defaultChecked={value.value}
              onChange={e => data[key].value = e.target.checked} />
          );
        else if (value.type === 'object')
          return (
            <SettingsSection key={key} data={value.value} />
          );
        // TODO show something more user friendly when an unrecognized type shows up
        return <p key={key}>{JSON.stringify(value)}</p>
      })}
    </Form.Group>
  );
}