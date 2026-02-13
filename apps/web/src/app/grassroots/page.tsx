import { redirect } from "next/navigation";

export default function GrassrootsPage() {
  redirect("/tournaments?category=grassroots");
}
