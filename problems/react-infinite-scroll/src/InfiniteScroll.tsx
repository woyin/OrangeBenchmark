interface InfiniteScrollProps {
  fetchData: (page: number) => Promise<{ items: any[]; hasMore: boolean }>
  renderItem: (item: any, index: number) => React.ReactNode
  loadingFallback?: React.ReactNode
  threshold?: number
}
export default function InfiniteScroll(props: InfiniteScrollProps) {
  return <div>InfiniteScroll</div>
}
