import { useMutation, useQuery } from "@tanstack/react-query";
import { ResponseError } from "./errors";
import { getServerEndpoint } from "./utils";

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
