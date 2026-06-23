import pyshark
from collections import defaultdict


class TCPConversationAnalyzer:
    def __init__(self, pcap_file: str, ip_filter: str = None):
        """
        Initialize the analyzer.

        :param pcap_file: Path to the .pcap file
        :param ip_filter: Optional IP address filter for display_filter
        """
        self.pcap_file = pcap_file
        self.ip_filter = ip_filter
        self.conversations = defaultdict(
            lambda: {"pkts": 0, "bytes": 0, "start": None, "end": None}
        )

    def _get_display_filter(self):
        if self.ip_filter:
            return f"ip.addr == {self.ip_filter}"
        return "tcp"

    def load_capture(self, file_path: str = None):
        """Load packets from the capture file with optional display filter."""
        if file_path:
            self.pcap_file = file_path

        display_filter = self._get_display_filter()
        self.cap = pyshark.FileCapture(self.pcap_file, display_filter=display_filter)
        return self

    def process_packets(self):
        """Parse packets and build TCP conversation stats."""
        for pkt in self.cap:
            try:
                stream_id = int(pkt.tcp.stream)
                size = int(pkt.length)
                ts = float(pkt.sniff_timestamp)
                c = self.conversations[stream_id]

                if c["start"] is None:
                    c["start"] = ts
                c["end"] = ts
                c["pkts"] += 1
                c["bytes"] += size

                if "src_ip" not in c:
                    c["src_ip"] = pkt.ip.src
                    c["src_port"] = int(pkt.tcp.srcport)
                    c["dst_ip"] = pkt.ip.dst
                    c["dst_port"] = int(pkt.tcp.dstport)

            except AttributeError:
                continue

        self.cap.close()
        return self

    def get_results(self):
        """Compute summary results per TCP stream."""
        results = []
        for sid, c in self.conversations.items():
            duration = c["end"] - c["start"]
            thrpt = (c["bytes"] * 8 / duration / 1e6) if duration > 0 else 0
            results.append(
                {
                    "stream_id": sid,
                    "src_ip": c.get("src_ip"),
                    "src_port": c.get("src_port"),
                    "dst_ip": c.get("dst_ip"),
                    "dst_port": c.get("dst_port"),
                    "packet_count": c["pkts"],
                    "byte_count": c["bytes"],
                    "duration_s": round(duration, 6),
                    "throughput_mbps": round(thrpt, 6),
                }
            )
        return results

    def print_summary(self):
        """Pretty-print summary for all streams."""
        for r in self.get_results():
            print(
                f"Stream {r['stream_id']:>3} | "
                f"{r['src_ip']}:{r['src_port']} → {r['dst_ip']}:{r['dst_port']} | "
                f"{r['packet_count']} pkts | {r['byte_count']} bytes | "
                f"{r['duration_s']} s | {r['throughput_mbps']} Mbps"
            )


# Example usage:
if __name__ == "__main__":
    analyzer = TCPConversationAnalyzer("capture.pcap", ip_filter="192.168.2.126")
    analyzer.load_capture().process_packets()
    # print(analyzer.get_results())
    analyzer.print_summary()
