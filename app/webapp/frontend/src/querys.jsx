import { useMutation, useQuery } from "@tanstack/react-query";
import { ResponseError } from "./errors";
import { getServerEndpoint } from "./utils";
import { Button, Spinner } from "react-bootstrap";
import { IconContext } from "react-icons/lib";
import { BsCheck2, BsXLg } from "react-icons/bs";

export const useFetchQuery = ({ queryKey, apiEndpoint, ...otherOptions }) => useQuery({
    queryKey,
    queryFn: async () => {
        const response = await fetch(apiEndpoint);
        if (!response.ok) {
            throw new ResponseError(response);
        }
        return await response.json();
    },
    ...otherOptions,
})

export const useServerQuery = ({ type, serverId }) => useFetchQuery({
    queryKey: ["servers", type, serverId],
    apiEndpoint: getServerEndpoint(type, serverId),
})

export const useFetchMutation = ({ apiEndpoint, method = "PUT", ...otherOptions }) => useMutation({
    mutationFn: async (payload) => {
        const response = await fetch(apiEndpoint, {
            method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            throw new ResponseError(response);
        }
        return await response.json();
    },
    ...otherOptions,
})

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