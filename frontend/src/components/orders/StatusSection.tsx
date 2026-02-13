import { useEffect, useState } from 'react';
import OrderCard, { Order, OrderStatus } from './OrderCard';

type StatusSectionProps = {
  status: OrderStatus;
  selectedOrderId: string | null;
  onSelectOrder: (orderId: string) => void;
};

export default function StatusSection({ status, selectedOrderId, onSelectOrder }: StatusSectionProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchOrders = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/orders?status=${status}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch ${status} orders: ${response.status}`);
        }

        const data: Order[] = await response.json();
        if (isMounted) {
          setOrders(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'An unexpected error occurred.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchOrders();

    return () => {
      isMounted = false;
    };
  }, [status]);

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold tracking-wide text-gray-800">{status}</h2>

      {loading && <p className="text-sm text-gray-500">Loading...</p>}

      {!loading && error && <p className="text-sm text-red-500">{error}</p>}

      {!loading && !error && orders.length === 0 && (
        <p className="text-sm text-gray-500">No orders in this status.</p>
      )}

      <div className="space-y-2">
        {!loading &&
          !error &&
          orders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              isSelected={selectedOrderId === order.id}
              onClick={onSelectOrder}
            />
          ))}
      </div>
    </section>
  );
}
