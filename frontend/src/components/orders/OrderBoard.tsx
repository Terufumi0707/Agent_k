import { useState } from 'react';
import StatusSection from './StatusSection';
import { OrderStatus } from './OrderCard';

const STATUSES: OrderStatus[] = ['DELIVERY', 'COORDINATE', 'BACKYARD'];

export default function OrderBoard() {
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);

  return (
    <div className="grid min-h-screen grid-cols-1 gap-4 bg-gray-100 p-4 md:grid-cols-[380px_1fr]">
      <aside className="space-y-4">
        {STATUSES.map((status) => (
          <StatusSection
            key={status}
            status={status}
            selectedOrderId={selectedOrderId}
            onSelectOrder={setSelectedOrderId}
          />
        ))}
      </aside>

      <main className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-lg font-semibold text-gray-900">Order Detail</h2>
        <p className="text-sm text-gray-600">
          {selectedOrderId
            ? `Selected order id: ${selectedOrderId}`
            : '詳細表示エリア（プレースホルダー）'}
        </p>
      </main>
    </div>
  );
}
