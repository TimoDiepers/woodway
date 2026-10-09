// Temporary map check (Task 7); Task 8 replaces this.
import { useEffect, useState } from "react";
import AtlasMap from "@/map/AtlasMap";
import { loadAtlas } from "@/data/load";
import { layerById } from "@/model/layers";
import type { Atlas } from "@/data/types";

export default function App() {
  const [at, setAt] = useState<Atlas | null>(null);
  useEffect(() => { loadAtlas().then(setAt).catch(console.error); }, []);
  return (
    <div className="fixed inset-0">
      {at && <AtlasMap atlas={at} layer={layerById("deltaT")} year={2100} cell={null} onCell={() => {}} />}
    </div>
  );
}
