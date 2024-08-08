import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";

import useAuth from "../hooks/useAuth";
import useAuthRefreshToken from "../hooks/useAuthRefreshToken";
import { Spinner } from "react-bootstrap";

// We know that we don't have an access token when the app first renders,
// because it is stored in memory and lost when the tab closes or refreshes.
// This means we need to refresh the token once here so we know if we're still signed in or not.
// After refresh token, we either have an access token and can render the page,
// or we don't, meaning that the refresh failed and we need to show the sign in page.
let checkedAuth = false;

export default function SignInRequired() {
    const { auth } = useAuth();
    const location = useLocation();
    const refreshToken = useAuthRefreshToken();

    // If an access token already exists, then don't bother checking auth again.
    // This could happen if the user logs in before they visit a protected page.
    if (auth.access_token) checkedAuth = true;

    useEffect(() => {
        if (checkedAuth) return;
        checkedAuth = true;
        refreshToken();
    }, [refreshToken]);

    if (!checkedAuth)
        return <Spinner />

    return auth.access_token ? <Outlet /> : <Navigate to={"/signin"} state={{ from: location }} replace />;
}