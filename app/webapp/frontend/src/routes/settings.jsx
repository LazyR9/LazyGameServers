import { Alert, Button, ButtonGroup, Container, Overlay, Spinner, Tooltip } from "react-bootstrap";
import { useFetchMutation, useFetchQuery } from "../querys";
import { useRef, useState } from "react";

import "./settings.css";
import { useQueryClient } from "@tanstack/react-query";
import { BsArrowRepeat, BsExclamationTriangle } from "react-icons/bs";
import { IconContext } from "react-icons/lib";

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
      </code>
      <Overlay target={target.current} show={show} placement="bottom" >
        {(props) => (
          <Tooltip
            {...props}
            className="unlimited-tooltip-width"
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

function GitBranchWarning() {
  const [show, setShow] = useState(false);
  const target = useRef(null);

  return (
    <span>
      <span
        className="ms-1 text-color-warning"
        ref={target}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        <IconContext.Provider value={{ color: "var(--bs-warning)" }}>
          <BsExclamationTriangle />
        </IconContext.Provider>
      </span>
      <Overlay target={target.current} show={show} placement="right">
        {(props) => (
          <Tooltip
            {...props}
            className="unlimited-tooltip-width"
            onMouseEnter={() => setShow(true)}
            onMouseLeave={() => setShow(false)}
          >
            Branch does not exist on remote!
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
              <p>
                Current commit: <GitCommitHash commitData={version.current} />
                {version.branch && (
                  <span>
                    {' '} on <code>{version.branch}</code>
                    {version.latest === null && <GitBranchWarning />}
                  </span>
                )}
              </p>
              {version.branch === null
                ? (
                  <Alert variant="warning">
                    <p>
                      WARNING: Your git HEAD is in a detached state!
                      Update checking will be unavailable until you reattach it.
                    </p>
                    <div className="text-end">
                      <Button>Checkout <code>main</code> Branch</Button>
                    </div>
                  </Alert>
                )
                : version.latest !== null &&
                  (version.commits_behind === 0
                    ? <p>You are on the latest version!</p>
                    : (
                      <>
                        <p>Latest commit: <GitCommitHash commitData={version.latest} /></p>
                        <p>You are {version.commits_behind} commits behind.</p>
                      </>
                    )
                  )
              }
              {updateMutation.isSuccess && <p>Update successful! Please rerun the install script to finish updating.</p>}

              {version.branch !== null && version.latest !== null &&
                (checkMutation.isPending
                  ? <Button disabled><Spinner size="sm" /></Button>
                  : (
                    <ButtonGroup>
                      {version.commits_behind > 0 && <Button onClick={() => updateMutation.mutate()}>Update</Button>}
                      <Button onClick={() => checkMutation.mutate()}>Check For Updates</Button>
                    </ButtonGroup>
                  )
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