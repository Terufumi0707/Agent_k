export type OrderStatus = 'DELIVERY' | 'COORDINATE' | 'BACKYARD';

export type Order = {
  id: string;
  session_id: string;
  current_status: OrderStatus;
};

type OrderCardProps = {
  order: Order;
  isSelected: boolean;
  onClick: (orderId: string) => void;
};

export default function OrderCard({ order, isSelected, onClick }: OrderCardProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(order.id)}
      className={`w-full rounded-lg border p-3 text-left transition ${
        isSelected
          ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
      }`}
    >
      <p className="text-xs text-gray-500">ID</p>
      <p className="mb-2 truncate font-medium text-gray-900">{order.id}</p>
      <p className="text-xs text-gray-500">Session ID</p>
      <p className="truncate text-sm text-gray-700">{order.session_id}</p>
    </button>
  );
}
