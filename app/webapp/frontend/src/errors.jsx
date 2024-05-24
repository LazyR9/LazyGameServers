import { useRouteError } from "react-router-dom";

export class ResponseError extends Error {
  constructor(response) {
    console.log(response)
    super(response.statusText);
    this.response = response;
  }
}

export default function ErrorPage({ title, subtitle, message, children }) {
  const error = useRouteError();
  if (error) console.error(error);

  const errorMessage = message || error?.statusText || error?.message;

  return (
    <div id="error-page">
      {children || <>
        <h1>{title || "Error!"}</h1>
        <p>{subtitle || "Sorry, an unexpected error has occurred."}</p>
      </>}
      {errorMessage && <>
        <p className="m-0">The details of the error are below:</p>
        <p>
          <code>{errorMessage}</code>
        </p>
      </>}
    </div>
  );
}