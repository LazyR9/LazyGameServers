import { useMutation, useQuery } from "@tanstack/react-query";
import { ResponseError } from "./errors";
import { getServerEndpoint } from "./utils";
import { Button, Spinner } from "react-bootstrap";
import { IconContext } from "react-icons/lib";
import { BsCheck2, BsXLg } from "react-icons/bs";
import useAuthFetch from "./hooks/useAuthFetch";

export function useJsonFetch({ endpoint, auth = false, method = "GET", ...fetchArgs }) {
    const authFetch = useAuthFetch();
    const fetchFn = auth ? authFetch : fetch;

    async function jsonFetch(payload) {
        const finalFetchArgs = {
            ...fetchArgs,
            method,
        }
        if (payload) {
            finalFetchArgs.headers = {
                ...finalFetchArgs.headers,
                "Content-Type": "application/json",
            };
            finalFetchArgs.body = JSON.stringify(payload);
        }
        const response = await fetchFn(endpoint, finalFetchArgs);
        if (!response.ok)
            throw new ResponseError(response);
        return await response.json();
    }

    return jsonFetch
}

export function useFetchQuery({ queryKey, apiEndpoint, auth = false, ...otherOptions }) {
    const jsonFetch = useJsonFetch({ endpoint: apiEndpoint, auth });
    return useQuery({
        queryKey,
        queryFn: () => jsonFetch(),
        ...otherOptions,
    });
}

export const useServerQuery = ({ type, serverId }) => useFetchQuery({
    queryKey: ["servers", type, serverId],
    apiEndpoint: getServerEndpoint(type, serverId),
    auth: true,
})

export function useFetchMutation({ apiEndpoint, method = "PUT", auth = false, ...otherOptions }) {
    const jsonFetch = useJsonFetch({ endpoint: apiEndpoint, auth, method })
    return useMutation({
        mutationFn: jsonFetch,
        ...otherOptions,
    });
}

export function MutationButton({ mutation, text = "Save", pending = <Spinner size="sm" />, success = <BsCheck2 />, error = <BsXLg />, ...props }) {
    return (
        <>
            <Button {...props} className={props.className + " me-2"} disabled={mutation.isPending}>
                {mutation.isPending ? pending : text}
            </Button>
            {mutation.isSuccess && (
                <IconContext.Provider value={{ color: "green", size: 25 }}>
                    {success}
                </IconContext.Provider>
            )}
            {mutation.isError && (
                <IconContext.Provider value={{ color: "red", size: 25 }}>
                    {error}
                </IconContext.Provider>
            )}
        </>
    );
}