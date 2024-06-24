import { useRouteError } from "react-router-dom";

export class ResponseError extends Error {
  constructor(response) {
    const url = new URL(response.url);
    super(`Got response "${response.status} ${response.statusText}" from ${url.pathname}`);
    this.response = response;
  }
}

export default function ErrorPage({ title, subtitle, message, children, error }) {
  const routerError = useRouteError();
  // if the passed error doesn't exist, try and use the router one
  if (!error)
    error = routerError;
  if (error) console.error(error);

  const errorMessage = message || error?.statusText || error?.message;

  return (
    <div id="error-page">
      <h1>{title || "Error!"}</h1>
      <p>{subtitle || "Sorry, an unexpected error has occurred."}</p>
      {errorMessage && <>
        <p className="m-0">The details of the error are below:</p>
        <p>
          <code>{errorMessage}</code>
        </p>
      </>}
      {children}
    </div>
  );
}