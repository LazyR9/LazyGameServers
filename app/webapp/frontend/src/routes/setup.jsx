import { Button, Container, Form } from "react-bootstrap";

import "./setup.css";
import { useState } from "react";
import CheckSetup from "../components/CheckSetup";
import { useFetchMutation } from "../querys";
import { useQueryClient } from "@tanstack/react-query";

export default function Setup() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(0);

  const mutation = useFetchMutation({ apiEndpoint: "/api/setup", method: "PUT" });
  const queryClient = useQueryClient();

  function handleSubmit(e) {
    e.preventDefault();

    // TODO this probably isn't the best way to do error handling but it works for now
    setError(0);

    if (password.length < 8) {
      setError((prev) => prev | 1);
    }

    if (password !== confirmPassword) {
      setError((prev) => prev | 2);
    }

    mutation.mutate({ password });
  }

  if (mutation.isSuccess)
    queryClient.setQueryData(["setup"], (prev) => ({ setup: true }))

  return (
    <Container className="setup-container">
      <CheckSetup isOnSetup />
      <h1>First Time Setup</h1>
      <h3>Set password</h3>
      <p>This password will give access to the entire app, so pick a secure one!</p>
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Password</Form.Label>
          <Form.Control type="password" value={password} onChange={(e) => setPassword(e.target.value)} isInvalid={error & 1} />
          <Form.Control.Feedback type="invalid">Password is not long enough!</Form.Control.Feedback>
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Confirm Password</Form.Label>
          <Form.Control type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} isInvalid={error & 2} />
          <Form.Control.Feedback type="invalid">Passwords do not match!</Form.Control.Feedback>
        </Form.Group>
        <div style={{ display: "inline-block" }}>
          <Button type="submit">Submit</Button>
        </div>
      </Form>
    </Container>
  );
}