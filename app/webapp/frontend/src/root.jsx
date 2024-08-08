import { Outlet, Link, NavLink } from "react-router-dom";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import Container from "react-bootstrap/Container";
import useAuth from "./hooks/useAuth";
import CheckSetup from "./components/CheckSetup";

export default function Root() {
  const { auth, setAuth } = useAuth();

  async function signOut() {
    fetch("/api/auth/logout", { method: "POST" });
    setAuth({});
  }

  return (
    <>
      <CheckSetup />
      <Navbar expand="sm" bg="primary">
        <Container fluid="xxl">
          <Navbar.Brand as={Link} to="/">
            Lazy Server Manager
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="navbar-nav" />
          <Navbar.Collapse id="navbar-nav">
            <Nav className="me-auto">
              <Nav.Link as={NavLink} to="/dashboard">Dashboard</Nav.Link>
            </Nav>
            <Nav>
              {auth.access_token ? <Nav.Link onClick={() => signOut()}>Sign Out</Nav.Link> : <Nav.Link as={NavLink} to="/signin">Sign In</Nav.Link>}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>
      <Container fluid="xxl" className="mt-3">
        <Outlet />
      </Container>
    </>
  )
}