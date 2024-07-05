export function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 Bytes'

  const k = 1000
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

export function getServerEndpoint(type, serverId) {
  return `/api/servers/${encodeURIComponent(type)}/${serverId}`;
}

export function makeEnum(array, starting_bit = 0) {
  return Object.freeze(array.reduce((object, value, index) => {
    let bit = starting_bit + index;
    let flag_value = bit === 0 ? 0 : 1 << (bit - 1);
    return {...object, [value]: flag_value}
  }, {}));
}
