import { ImageResponse } from "next/og";

export const alt = "Invoice Processing";
export const contentType = "image/png";
export const size = {
  width: 180,
  height: 180
};

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "center",
          background: "#174e3b",
          borderRadius: 32,
          color: "#fffef9",
          display: "flex",
          fontFamily: "Arial, sans-serif",
          fontSize: 88,
          fontWeight: 800,
          height: "100%",
          justifyContent: "center",
          letterSpacing: -8,
          paddingRight: 8,
          width: "100%"
        }}
      >
        IP
      </div>
    ),
    size
  );
}
