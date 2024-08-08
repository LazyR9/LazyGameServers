import { Navigate } from "react-router-dom";
import { useFetchQuery } from "../querys";

export default function CheckSetup({ isOnSetup = false }) {
  // We want this to never go stale - this value should only get changed on the server once!
  const { isLoading, data } = useFetchQuery({ queryKey: ["setup"], apiEndpoint: "/api/setup", staleTime: Infinity });

  if (!isLoading) {
    if (!data.setup) {
      if (!isOnSetup) {
        return <Navigate to="/setup" replace />
      }
    } else {
      if (isOnSetup) {
        return <Navigate to="/" replace />
      }
    }
  }
}