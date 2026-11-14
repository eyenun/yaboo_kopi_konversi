import 'package:flutter_test/flutter_test.dart';
import 'package:yaboo_kopi_konversi/main.dart';

void main() {
  testWidgets('Pengujian navigasi 3 halaman utama Yaboo Kopi', (WidgetTester tester) async {
    await tester.pumpWidget(const YabooKopiApp());

    expect(find.text('Yaboo Kopi Analytics'), findsOneWidget);
    expect(find.text('Unggah Data Transaksi POS'), findsOneWidget);

    await tester.tap(find.text('Dasbor'));
    await tester.pumpAndSettle();
    expect(find.text('Dasbor Analitik & Prediksi Stok'), findsOneWidget);

    await tester.tap(find.text('AI Advisor'));
    await tester.pumpAndSettle();
    expect(find.text('AI Advisor Perencanaan Belanja'), findsOneWidget);
  });
}