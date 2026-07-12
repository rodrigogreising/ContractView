export const roleLabel = (role: string) =>
  role
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
