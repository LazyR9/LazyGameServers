import { useQuery } from "@tanstack/react-query";
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