import { Badge, Button, Card, CardText, Form, Modal } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { BsFillPlayFill, BsFillStopFill } from 'react-icons/bs';
import { IconContext } from 'react-icons/lib';

import { formatBytes } from '../utils';

import './dashboard.css';
import { useFetchMutation, useFetchQuery } from '../querys';
import { ServerControls, ServerIndicator } from './server';
import { useState } from 'react';

export default function Dashboard() {
  return (
    <>
      <h3>Servers</h3>
      <ServerList />
    </>
  )
}

export function ServerList() {
  const { isPending, isError, data: servers, error } = useFetchQuery({
    queryKey: ['servers'],
    apiEndpoint: '/api/servers',
    auth: true,
    // TODO make the refetch interval user configurable
    refetchInterval: 10000,
  });

  if (isPending) {
    return <span>Loading...</span>
  }

  if (isError) {
    return <span>Error: {error.message}</span>
  }

  // TODO should servers use a unique id?
  // currently they use a unique game and id combo
  return (
    <>
      <div className='mx-3'>
        <div className='mb-2'>
          {servers.map((server) => <ServerListItem server={server} key={server.game.value + ':' + server.id.value} />)}
        </div>
        <NewServerButton />
      </div>
    </>
  );
}

export function NewServerButton() {
  const [show, setShow] = useState(false);

  const mutation = useFetchMutation({ apiEndpoint: "/api/servers", method: "POST", auth: true });

  return (
    <>
      <Button onClick={() => setShow(true)}>New</Button>
      <Modal show={show} onHide={() => setShow(false)} centered>
        <Modal.Header>
          <Modal.Title>New Server</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form id='new-server-form' onSubmit={(e) => {
            e.preventDefault();
            console.log(e.target[0].value)
            console.log(e.target[1].value)
            mutation.mutate({ id: e.target[0].value, type: e.target[1].value });
          }}>
            <Form.Group>
              <Form.Label>ID</Form.Label>
              <Form.Control />
            </Form.Group>
            <Form.Group>
              <Form.Label>Type</Form.Label>
              <Form.Control />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant='secondary' onClick={() => setShow(false)}>Cancel</Button>
          <Button type='submit' form='new-server-form' onClick={() => setShow(false)}>Create</Button>
        </Modal.Footer>
      </Modal>
    </>
  )
}

export function ServerListItem({ server }) {
  return (
    <Link className='undo-a-tag' to={`/servers/${encodeURIComponent(server.game.value)}/${server.id.value}`}>
      <div className='row hover seperate-cells rounded text-center py-2 align-children-center'>
        <div className="col-sm-2"><span className='h5'>{server.id.value}</span> <Badge bg='secondary'>{server.game.value}</Badge></div>
        <div className="col-sm-auto">
          <div className="row gx-0 align-children-center-flex justify-content-center" onClick={(e) => {
            e.preventDefault();
          }}>
            <div className="col-auto me-3">
              <ServerIndicator server={server} />
            </div>
            <div className="col-auto">
              <IconContext.Provider value={{ size: 20 }}>
                <ServerControls server={server} size="sm">
                  <BsFillPlayFill />
                  <BsFillStopFill />
                </ServerControls>
              </IconContext.Provider>
            </div>
          </div>
        </div>
        <div className="col-sm">
          <ServerListItemStats stats={server.stats.value} />
        </div>
      </div>
    </Link>
  )
}

export function ServerListItemStats({ stats }) {
  return (
    <div className="row align-children-center">
      <div className="col">Players: <span className='text-nowrap'>{stats.players || '-'} / {stats.max_players || '-'}</span></div>
      <div className="col">CPU Usage: {stats.cpu}%</div>
      <div className="col">Memory Usage: {formatBytes(stats.memory)}</div>
    </div>
  );
}

export function ServerCard({ server }) {
  // TODO get subtitle on same line as title
  // TODO add some sort of hover effect on card? (like a slight color tint) might not actually look good...
  return (
    <Card>
      <Card.Header>
        {server.id}
        <Badge bg='secondary' className='ms-2'>
          {server.game}
        </Badge>
      </Card.Header>
      <Card.Body>
        <CardText>
          cool stats and stuff
        </CardText>
      </Card.Body>
    </Card>
  )
}