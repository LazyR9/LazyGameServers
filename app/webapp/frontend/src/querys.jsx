import { useQuery } from "@tanstack/react-query";
import { ResponseError } from "./errors";

export const useFetchQuery = ({queryKey, apiEndpoint, ...otherOptions}) => useQuery({
    queryKey: queryKey,
    queryFn: async () => {
        const response = await fetch(apiEndpoint);
        if (!response.ok) {
            throw new ResponseError(response);
        }
        return await response.json();
    },
    ...otherOptions,
})