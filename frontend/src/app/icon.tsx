import { ImageResponse } from "next/og";

export const alt = "Invoice Processing";
export const contentType = "image/png";
export const size = {
  width: 32,
  height: 32
};

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "center",
          background: "#174e3b",
          color: "#fffef9",
          display: "flex",
          fontFamily: "Arial, sans-serif",
          fontSize: 18,
          fontWeight: 800,
          height: "100%",
          justifyContent: "center",
          width: "100%"
        }}
      >
        IP
      </div>
    ),
    size
  );
}
