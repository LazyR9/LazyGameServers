import { Outlet, Link } from "react-router-dom";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import Container from "react-bootstrap/Container";

export default function Root() {
  return (
    <>
      <Navbar expand="sm" bg="primary">
        <Container fluid="xxl">
          <Navbar.Brand as={Link} to="/">
            Lazy Server Manager
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="navbar-nav" />
          <Navbar.Collapse id="navbar-nav">
            <Nav className="me-auto">
              <Nav.Link as={Link} to="/dashboard">Dashboard</Nav.Link>
            </Nav>
            <Nav>
              Sign In
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