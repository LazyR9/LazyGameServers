import { forwardRef, useRef, useState } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import useWebSocket from "react-use-websocket";
import useAuth from "../hooks/useAuth";
import useAuthRefreshToken from "../hooks/useAuthRefreshToken";

import "./Wizard.css";

const RangeSlider = forwardRef(function ({ min, max, step }, ref) {
  const [sliderValue, setSliderValue] = useState(min);
  const [inputValue, setInputValue] = useState(min);
  const [invalidInput, setInvalidInput] = useState(false);

  function onInput(e) {
    const value = e.target.value;
    if (value >= min && value <= max) {
      setSliderValue(value);
      setInvalidInput(false);
    } else {
      setInvalidInput(true);
    }
    setInputValue(value);
  }

  function onSlider(e) {
    setSliderValue(e.target.value);
    setInputValue(e.target.value);
  }

  return (
    <>
      <Form.Range ref={ref} min={min} max={max} step={step} value={sliderValue} onChange={onSlider} />
      <div className="center-middle-element">
        <span className="align-content-center">
          <span className="float-start">
            {min}
          </span>
        </span>
        <Form.Control type="number" size="sm" isInvalid={invalidInput} min={min} max={max} className="mx-1 w-auto" step={step} value={inputValue} onChange={onInput} />
        <span className="align-content-center">
          <span className="float-end">
            {max}
          </span>
        </span>
      </div>
    </>
  );
});

function getInput(input, refs, i) {
  const ref = el => refs.current[i] = el;
  // TODO should input type really be ignored completely when there is a select multiple?
  if (input.validation_data.choices)
    return <Form.Select ref={ref}>{input.validation_data.choices.map((value) => <option key={value}>{value}</option>)}</Form.Select>

  const min = input.validation_data.min;
  const max = input.validation_data.max;
  if (min && max)
    return <RangeSlider ref={ref} min={min} max={max} step={input.validation_data.step} />

  switch (input.input_type) {
    case "BOOL":
      return <Form.Check ref={ref} />
    default:
      return <Form.Control ref={ref} />;
  }

}

export default function Wizard({ show, onHide, url, host }) {
  // TODO do we need this many states?
  // something like loading could be infered from if other states are null or not...
  const [inputs, setInputs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [finished, setFinished] = useState(false);
  const [message, setMessage] = useState(null);
  const [retries, setRetries] = useState({});
  const [shouldReconnect, setShouldReconnect] = useState(true);

  const finalHost = host || (process.env.NODE_ENV !== "development" ? window.location.host : "localhost:8000");
  const fullUrl = (window.location.protocol === "https" ? "wss" : "ws") + '://' + finalHost + url;

  const { auth } = useAuth();
  const refreshToken = useAuthRefreshToken();
  const { sendJsonMessage } = useWebSocket(fullUrl, {
    onMessage: (event) => {
      const data = JSON.parse(event.data);
      setLoading(false);
      switch (data?.type) {
        case "input":
          setInputs([data]);
          break;
        case "input_multiple":
          setInputs(data.inputs);
          break;
        case "message":
          setMessage(data);
          break;
        case "finish":
          setFinished(true);
          setMessage(data.message);
          break;
        case "retry":
          setRetries({ mesages: [data.message] });
          break;
        case "retry_multiple":
          setRetries(data)
          break;
        default:
          console.warn(`Unrecognized event type ${data.type}!`)
          break;
      }
    },
    onOpen: (event) => {
      event.target.send(auth.access_token);
    },
    onError: (event) => {
      console.error(event);
    },
    onClose: async (event) => {
      // If the socket closed with 3000 (unauthorized), then don't reconnect
      if (event.code === 3000) {
        if (await refreshToken() === undefined) {
          setMessage("Error: You are not authorized to access this wizard!");
          setLoading(false);
          setFinished(true);
          setShouldReconnect(false);
        }
      }
    },
    shouldReconnect: () => shouldReconnect,
  }, show);

  const refs = useRef([]);

  function onNext() {
    if (message !== null) {
      setMessage(null);
      return;
    }
    let values = [];
    for (const i in inputs) {
      const input = inputs[i];
      switch (input.input_type) {
        case "STRING":
          values.push(refs.current[i].value);
          break;
        case "BOOL":
          values.push(refs.current[i].checked);
          break;
        case "NUMBER":
          values.push(parseFloat(refs.current[i].value));
          break;
        default:
          break;
      }
    }
    sendJsonMessage(inputs.length === 1 ? { type: "response", value: values[0] } : { type: "response_multiple", values });
    setLoading(true);
    setRetries([]);
  }

  function cancel() {
    sendJsonMessage({ type: "cancel" });
    onHide && onHide();
  }


  return (
    <Modal show={show} centered>
      <Modal.Header>
        <Modal.Title>
          Wizard
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {loading
          ? <center><Spinner /></center>
          : finished
            ? (
              <center>
                {message || "Setup Complete!"}
              </center>
            )
            : message
              ? <center>{message}</center>
              : <>
                {retries.message && <Alert variant="danger">{retries.message}</Alert>}
                {inputs.map((input, index) => {
                  const retry = retries.messages?.[index];
                  return <Form.Group key={index}>
                    {retry && <Alert variant="danger">{retry}</Alert>}
                    <Form.Label>{input.message}</Form.Label>
                    {getInput(input, refs, index)}
                  </Form.Group>
                })}
              </>
        }
      </Modal.Body>
      <Modal.Footer>
        {finished
          ? <Button variant="primary" onClick={() => onHide && onHide()}>Finish</Button>
          : (
            <>
              <Button variant="secondary" onClick={cancel}>Cancel</Button>
              <Button disabled={loading} variant="primary" onClick={() => onNext()}>Next</Button>
            </>
          )
        }
      </Modal.Footer>
    </Modal>
  );
}