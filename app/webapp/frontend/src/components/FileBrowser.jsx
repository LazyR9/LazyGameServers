import { Button, Form, ListGroup, Spinner } from "react-bootstrap";
import { BsArrowLeft, BsCheck2, BsFileEarmarkFill, BsFillFolderFill, BsFillQuestionSquareFill, BsXLg } from "react-icons/bs";
import { IconContext } from "react-icons/lib";

import { useFetchQuery } from "../querys"
import { getServerEndpoint } from "../utils";
import { Link, useLocation, useParams } from "react-router-dom";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ResponseError } from "../errors";

export default function ServerFileBrowser() {
  const { type, serverId, "*": path } = useParams();

  const queryKey = ["servers", type, serverId, "files", path];
  const apiEndpoint = getServerEndpoint(type, serverId) + '/files/' + path;
  const { isPending, data: file } = useFetchQuery({ queryKey, apiEndpoint });

  if (isPending) return <div style={{textAlign: "center"}}><Spinner /></div>

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

function FileItem({ file }) {
  // FIXME This is a workaround because react router's v7_relativeSplatPath flag doesn't work properly.
  // (issue link: https://github.com/remix-run/react-router/issues/11629)
  const { pathname } = useLocation();
  let link = pathname + '/' + file.name;
  // react router just lets the ".." through to the a tag without changing it,
  // so we manually resolve this to make sure there isn't a trailing slash,
  // as that messes with react query's caching
  if (link.endsWith('..')) {
    const split_path = link.split('/');
    split_path.pop(); // pop off the ".."
    split_path.pop(); // then whatever is behind it
    link = split_path.join('/');
  }
  return (
    <ListGroup.Item as={Link} to={link} relative="path">
      <FileIcon type={file.type} />
      <span className="ps-3">{file.name}</span>
    </ListGroup.Item>
  );
}

function File({ file, apiEndpoint }) {
  const [contents, setContents] = useState(file.contents);
  const mutation = useMutation({
    mutationFn: async (contents) => {
      const response = await fetch(apiEndpoint, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ contents }),
      });
      if (!response.ok) {
        throw new ResponseError(response);
      }
      return await response.json();
    }
  })

  // FIXME same as above
  const { pathname } = useLocation();
  const link = pathname.endsWith('/') ? pathname + ".." : pathname + "/..";

  return (
    <div>
      <h4><Link to={link}><BsArrowLeft /></Link><span className="ps-1">{file.name}</span></h4>
      <Form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate(contents);
        }}
      >
        <Form.Group>
          <Button type="submit" className="mb-2 me-2" disabled={mutation.isPending}>
            {mutation.isPending ? <Spinner size="sm" /> : "Save"}
          </Button>
          {mutation.isSuccess && (
            <IconContext.Provider value={{ color: "green", size: 25 }}>
              <BsCheck2 />
            </IconContext.Provider>
          )}
          {mutation.isError && (
            <IconContext.Provider value={{ color: "red", size: 25 }}>
              <BsXLg />
            </IconContext.Provider>
          )}
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