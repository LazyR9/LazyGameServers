import { Button, ButtonGroup, Container, Overlay, Spinner, Tooltip } from "react-bootstrap";
import { useFetchMutation, useFetchQuery } from "../querys";
import { useRef, useState } from "react";

import "./settings.css";
import { useQueryClient } from "@tanstack/react-query";

function GitCommitHash({ commitData }) {
  const [show, setShow] = useState(false);
  const target = useRef(null);

  return (
    <span>
      <code
        className="version"
        variant="link"
        ref={target}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => navigator.clipboard.writeText(commitData.hash)}
      >
        {commitData.short_hash}
      </code> on <code>{commitData.branch}</code>
      <Overlay target={target.current} show={show} placement="bottom" >
        {(props) => (
          <Tooltip
            {...props}
            className="version-tooltip"
            onMouseEnter={() => setShow(true)}
            onMouseLeave={() => setShow(false)}
          >
            {commitData.hash}
          </Tooltip>
        )}
      </Overlay>
    </span>
  );
}

export default function Settings() {
  const { isSuccess, isLoading, data: version, error } = useFetchQuery({ queryKey: ["version"], apiEndpoint: "/api/settings/version" });

  const queryClient = useQueryClient();

  const checkMutation = useFetchMutation({
    apiEndpoint: "/api/settings/version/check",
    method: "POST",
    onSuccess: (data) => {
      queryClient.setQueryData(["version"], data);
    },
    onError: (error) => console.error(error),
  })

  const updateMutation = useFetchMutation({
    apiEndpoint: "/api/settings/version/update",
    method: "POST",
  })

  return (
    <Container>
      <h1 className="mb-4">Settings</h1>
      <div className="settings-container rounded p-3">
        <h3>Version</h3>
        {isLoading
          ? <p>Loading...</p>
          : (isSuccess
            ? <>
              <p>Current commit: <GitCommitHash commitData={version.current} /></p>
              {version.commits_behind === 0
                ? <p>You are on the latest version!</p>
                : (
                  <>
                    <p>Latest commit: <GitCommitHash commitData={version.latest} /></p>
                    <p>You are {version.commits_behind} commits behind.</p>
                  </>
                )
              }
              {updateMutation.isSuccess && <p>Update successful! Please rerun the install script to finish updating.</p>}

              {checkMutation.isPending
                ? <Button disabled><Spinner size="sm" /></Button>
                : (
                  <ButtonGroup>
                    {version.commits_behind > 0 && <Button onClick={() => updateMutation.mutate()}>Update</Button>}
                    <Button onClick={() => checkMutation.mutate()}>Check For Updates</Button>
                  </ButtonGroup>
                )
              }
              {updateMutation.isError && <span className="ms-2 text-danger">Error while updating: {updateMutation.error.message}</span>}
              {checkMutation.isError && <span className="ms-2 text-danger">Unable to get updates!</span>}
            </>
            : <p>Error: {error.message}</p>
          )
        }
      </div>
    </Container>
  )
}