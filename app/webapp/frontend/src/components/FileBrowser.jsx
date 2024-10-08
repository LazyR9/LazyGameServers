import { Button, Form, ListGroup, Spinner } from "react-bootstrap";
import { BsArrowLeft, BsFileEarmarkFill, BsFillFolderFill, BsFillQuestionSquareFill } from "react-icons/bs";
import { IconContext } from "react-icons/lib";

import { MutationButton, useFetchMutation, useFetchQuery } from "../querys"
import { getServerEndpoint } from "../utils";
import { Link, useLocation, useParams } from "react-router-dom";
import { useState } from "react";
import ErrorPage, { ResponseError } from "../errors";

import "./FileBrowser.css";

export default function ServerFileBrowser() {
  const { type, serverId, "*": path } = useParams();

  const queryKey = ["servers", type, serverId, "files", path];
  const apiEndpoint = getServerEndpoint(type, serverId) + '/files/' + path;
  const { isPending, isError, error, data: file } = useFetchQuery({ queryKey, apiEndpoint, auth: true });

  if (isPending) return <div style={{ textAlign: "center" }}><Spinner /></div>

  if (isError) {
    if (error instanceof ResponseError) {
      if (error.response.status === 404)
        return (
          <ErrorPage title="Unknown file!" subtitle={<>The file <code>/{path}</code> doesn't exist on the server!</>}>
            {/* TODO implement this */}
            <Button onClick={() => alert("not implemented yet!")}>Create File</Button>
            {/* This relies on the buggy behaviour of splat paths and relative links (see useWorkaround),
                and will need to be updated once that is fixed. */}
            <Button as={Link} to="." className="ms-2">Root Folder</Button>
          </ErrorPage>
        )
    }
    return <ErrorPage error={error} />
  }

  switch (file.type) {
    case "DIRECTORY":
      return <Directory directory={file} path={path} />
    case "FILE":
      return <File file={file} apiEndpoint={apiEndpoint} />
    default:
      // TODO there are a few placeholders like this around that I need to replace with proper error messages
      return <p>unknown file type</p>
  };
}

function Directory({ directory, path }) {
  return (
    <IconContext.Provider value={{ color: "#aaaaaa" }}>
      <ListGroup>
        {path !== '' && <FileItem file={{ name: "..", type: "DIRECTORY" }} />}
        {directory.files.map(file => (
          <FileItem file={file} key={file.name} />
        ))}
      </ListGroup>
    </IconContext.Provider>
  );
}

function FileIcon({ type }) {
  switch (type) {
    case "DIRECTORY":
      return <BsFillFolderFill />;
    case "FILE":
      return <BsFileEarmarkFill />;
    default:
      return <BsFillQuestionSquareFill />;
  };
}

function useWorkaround(relativePath) {
  // FIXME This is a workaround because react router's v7_relativeSplatPath flag doesn't work properly.
  // (issue link: https://github.com/remix-run/react-router/issues/11629)
  const { pathname } = useLocation();
  let link = pathname + '/' + relativePath;
  // react router just lets the ".." through to the a tag without changing it,
  // so we manually resolve this to make sure there isn't a trailing slash,
  // as that messes with react query's caching
  if (link.endsWith('..')) {
    const split_path = link.split('/');
    split_path.pop(); // pop off the ".."
    split_path.pop(); // then whatever is behind it
    link = split_path.join('/');
  }
  return link;
}

function FileItem({ file }) {
  const link = useWorkaround(file.name);
  return (
    <ListGroup.Item as={Link} to={link} relative="path">
      <FileIcon type={file.type} />
      <span className="ps-3">{file.name}</span>
    </ListGroup.Item>
  );
}

function File({ file, apiEndpoint }) {
  const [contents, setContents] = useState(file.contents);
  const mutation = useFetchMutation({ apiEndpoint, auth: true });

  const link = useWorkaround("..");

  return (
    <div>
      <h4><Link to={link}><BsArrowLeft /></Link><span className="ps-1">{file.name}</span></h4>
      <Form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate({ contents });
        }}
      >
        <Form.Group>
          <MutationButton mutation={mutation} type="submit" className="mb-2" />
          <Form.Control
            className="file-input"
            as="textarea"
            value={contents}
            onChange={e => setContents(e.target.value)}
            rows={contents.split('\n').length}
            spellCheck={false}
            autoCapitalize="off"
          />
        </Form.Group>
      </Form>
    </div>
  );
}