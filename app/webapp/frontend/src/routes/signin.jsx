import { useContext, useState } from "react";
import { Button, Form } from "react-bootstrap";
import AuthContext from "../context/AuthProvider";
import { useLocation, useNavigate } from "react-router-dom";

export default function SignIn() {
  const [password, setPassword] = useState('');

  const { setAuth } = useContext(AuthContext);

  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/";

  async function handleSignin(e) {
    e.preventDefault();

    const formBody = new URLSearchParams();
    formBody.append("username", "admin");
    formBody.append("password", password)

    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formBody,
    });

    const json = await response.json();

    setAuth(json);
    navigate(from, { replace: true });
  }

  return (
    <div>
      <h1>Sign In</h1>
      <Form onSubmit={handleSignin}>
        <Form.Group className="mb-3">
          <Form.Label htmlFor="password">Password</Form.Label>
          <Form.Control type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </Form.Group>
        <Button variant="primary" type="submit">Sign In</Button>
      </Form>
    </div>
  );
}