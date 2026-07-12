export const roleLabel = (role: string) =>
  role.split("_").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");
