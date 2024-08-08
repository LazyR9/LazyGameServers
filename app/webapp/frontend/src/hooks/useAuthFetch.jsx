import useAuth from "./useAuth";
import useAuthRefreshToken from "./useAuthRefreshToken";

export default function useAuthFetch() {

    const { auth } = useAuth();
    const refreshToken = useAuthRefreshToken();

    function authFetch() {
        let args = arguments;
        if (!args[1]?.headers?.["Authorization"]) {
            args[1] = {
                ...args[1],
                headers: {
                    ...args[1]?.headers,
                    "Authorization": `Bearer ${auth.access_token}`,
                }
            };
        }
        args.length = 2;
        
        return fetch(...args).then(async function (response) {
            if (response.status === 401) {
                const { access_token: newAccessToken } = await refreshToken();
                args[1].headers["Authorization"] = `Bearer ${newAccessToken}`;
                return fetch(...args);
            }
            return response;
        })
    }

    return authFetch;

}