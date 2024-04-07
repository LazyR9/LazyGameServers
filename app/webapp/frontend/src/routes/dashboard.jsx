import Card from 'react-bootstrap/Card';
import CardText from 'react-bootstrap/CardText';
import Badge from 'react-bootstrap/Badge';
import { useQuery } from '@tanstack/react-query';

import { formatBytes } from '../utils';

import './dashboard.css';

export default function Dashboard() {
  return (
    <>
      <h3>Servers</h3>
      <ServerList />
    </>
  )
}

export function ServerList() {
  const { isPending, isError, data: servers, error } = useQuery({
    queryKey: ['servers'],
    queryFn: async () => {
      return await fetch('/api/servers').then(res => res.json());
    }
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
    <div className='mx-3'>
      {servers.map((server) => (
        <div key={server.game + ':' + server.id} className='row hover seperate-cells rounded text-center py-2'>
          <div className="col-sm-2"><p className='h5 d-inline-block mb-0'>{server.id}</p> <Badge bg='secondary'>{server.game}</Badge></div>
          <div className="col-sm">
            <div className="row align-children-center">
              <div className="col">Players: <span className='text-nowrap'>{server.players} / {server.max_players}</span></div>
              <div className="col">CPU Usage: {server.cpu}%</div>
              <div className="col">Memory Usage: {formatBytes(server.memory)}</div>
            </div>
          </div>
          <div className="col-sm-2">this is a description</div>
        </div>
      ))}
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