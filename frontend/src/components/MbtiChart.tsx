"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, Text } from 'recharts';

interface MbtiChartProps {
  data: Record<string, number>;
}

export default function MbtiChart({ data }: MbtiChartProps) {
  // data format: { 'I/E': 0.8, 'S/N': 0.2, ... }
  // Transform for Recharts
  const chartData = [
    { name: 'I/E', value: data['I/E'] * 100, label: 'I 성향' },
    { name: 'S/N', value: data['S/N'] * 100, label: 'S 성향' },
    { name: 'T/F', value: data['T/F'] * 100, label: 'T 성향' },
    { name: 'P/J', value: data['P/J'] * 100, label: 'P 성향' },
  ].reverse();

  const colors = ['#4f46e5', '#10b981', '#f59e0b', '#ec4899'];

  return (
    <div className="h-[300px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
        >
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            dataKey="name"
            type="category"
            tick={{ fill: 'currentColor', fontSize: 12 }}
            width={40}
          />
          <Tooltip
            cursor={{ fill: 'transparent' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white dark:bg-slate-800 p-2 border border-slate-200 dark:border-slate-700 rounded shadow-sm text-xs">
                    <p className="font-bold">{payload[0].payload.label}</p>
                    <p>{`${Number(payload[0].value || 0).toFixed(1)}%`}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-[10px] text-center text-slate-500 mt-2">
        ※ 오른쪽일수록 I / S / T / P 성향이 강함을 의미합니다.
      </p>
    </div>
  );
}
