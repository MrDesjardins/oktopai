import { useState } from "react";

export default function Page() {
  const [open, setOpen] = useState(false);
  return <button onClick={() => setOpen(!open)}>{String(open)}</button>;
}
