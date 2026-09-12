import { useState } from "react";
import { View, Text, LayoutChangeEvent } from "react-native";
import Svg, { Circle, Line, Path, Rect } from "react-native-svg";

const HEIGHT = 160;
const PAD = { top: 12, right: 8, bottom: 20, left: 8 };

function useWidth(): [number, (e: LayoutChangeEvent) => void] {
  const [w, setW] = useState(0);
  return [w, (e) => setW(e.nativeEvent.layout.width)];
}

function scaleY(v: number, max: number, h: number) {
  if (max <= 0) return h - PAD.bottom;
  const usable = h - PAD.top - PAD.bottom;
  return PAD.top + usable * (1 - v / max);
}

/** Two-series line chart (RD 2.3 — daily ad views vs QR scans). */
export function LineChartDual({
  series,
  aKey,
  bKey,
  aLabel,
  bLabel,
}: {
  series: Record<string, number | string>[];
  aKey: string;
  bKey: string;
  aLabel: string;
  bLabel: string;
}) {
  const [width, onLayout] = useWidth();
  const pts = series.length;
  const max = Math.max(
    1,
    ...series.map((r) => Math.max(Number(r[aKey]), Number(r[bKey]))),
  );
  const innerW = Math.max(0, width - PAD.left - PAD.right);
  const x = (i: number) =>
    PAD.left + (pts > 1 ? (innerW * i) / (pts - 1) : innerW / 2);

  const path = (key: string) =>
    series
      .map(
        (r, i) =>
          `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${scaleY(
            Number(r[key]),
            max,
            HEIGHT,
          ).toFixed(1)}`,
      )
      .join(" ");

  return (
    <View onLayout={onLayout}>
      {width > 0 ? (
        <Svg width={width} height={HEIGHT}>
          <Line
            x1={PAD.left}
            y1={HEIGHT - PAD.bottom}
            x2={width - PAD.right}
            y2={HEIGHT - PAD.bottom}
            stroke="#334155"
            strokeWidth={1}
          />
          <Path d={path(aKey)} stroke="#2563eb" strokeWidth={2} fill="none" />
          <Path d={path(bKey)} stroke="#22c55e" strokeWidth={2} fill="none" />
          {series.map((r, i) => (
            <Circle
              key={`a${i}`}
              cx={x(i)}
              cy={scaleY(Number(r[aKey]), max, HEIGHT)}
              r={2}
              fill="#2563eb"
            />
          ))}
        </Svg>
      ) : (
        <View style={{ height: HEIGHT }} />
      )}
      <View className="mt-1 flex-row gap-4">
        <Legend color="#2563eb" label={aLabel} />
        <Legend color="#22c55e" label={bLabel} />
      </View>
    </View>
  );
}

/** Horizontal-ish bar chart for a small category/time-slot breakdown. */
export function BarBreakdown({
  data,
}: {
  data: { label: string; value: number }[];
}) {
  const [width, onLayout] = useWidth();
  const max = Math.max(1, ...data.map((d) => d.value));
  const gap = 10;
  const barW =
    data.length > 0
      ? Math.max(
          8,
          (width - PAD.left - PAD.right - gap * (data.length - 1)) / data.length,
        )
      : 0;

  return (
    <View onLayout={onLayout}>
      {width > 0 ? (
        <Svg width={width} height={HEIGHT}>
          {data.map((d, i) => {
            const h =
              (HEIGHT - PAD.top - PAD.bottom) * (d.value / max);
            const bx = PAD.left + i * (barW + gap);
            return (
              <Rect
                key={d.label}
                x={bx}
                y={HEIGHT - PAD.bottom - h}
                width={barW}
                height={Math.max(0, h)}
                rx={3}
                fill="#2563eb"
              />
            );
          })}
        </Svg>
      ) : (
        <View style={{ height: HEIGHT }} />
      )}
      <View className="mt-1 flex-row justify-between">
        {data.map((d) => (
          <Text key={d.label} className="text-[10px] text-muted">
            {d.label} ({d.value})
          </Text>
        ))}
      </View>
    </View>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <View className="flex-row items-center gap-1">
      <View
        style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: color }}
      />
      <Text className="text-xs text-muted">{label}</Text>
    </View>
  );
}
