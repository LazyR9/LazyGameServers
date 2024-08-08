import useAuth from "./useAuth";

export default function useAuthRefreshToken() {

    const { setAuth } = useAuth();

    async function refreshToken() {
        const response = await fetch("/api/auth/refresh", { method: "POST" });
        if (response.status === 401) {
            setAuth({});
            return;
        }
        const data = await response.json();
        setAuth(data);
        return data;
    }

    return refreshToken;

}