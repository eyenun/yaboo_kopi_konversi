import 'package:flutter/material.dart';

void main() {
  runApp(const YabooKopiApp());
}

class YabooKopiApp extends StatelessWidget {
  const YabooKopiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Yaboo Kopi - AI Inventory & Cashflow',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.brown),
        useMaterial3: true,
      ),
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;

  // 3 Skeleton Screen utama sesuai target Sprint 1 Project Plan
  final List<Widget> _pages = const [
    UploaderSkeletonPage(),   // Area Frontend & Data Wrangling (Ahmad & Gaida)
    DashboardSkeletonPage(),  // Area Visualisasi Analitik (Tim DS)
    AIAdvisorSkeletonPage(),  // Area Next-Gen AI Engineer (Nur Ainun)
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Yaboo Kopi Analytics'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: _pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (int index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.upload_file),
            label: 'Upload CSV',
          ),
          NavigationDestination(
            icon: Icon(Icons.bar_chart),
            label: 'Dasbor',
          ),
          NavigationDestination(
            icon: Icon(Icons.smart_toy),
            label: 'AI Advisor',
          ),
        ],
      ),
    );
  }
}

// 1. SKELETON HALAMAN UPLOADER CSV
class UploaderSkeletonPage extends StatelessWidget {
  const UploaderSkeletonPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_upload_outlined, size: 64, color: Colors.brown),
            const SizedBox(height: 16),
            const Text(
              'Unggah Data Transaksi POS',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Pilih berkas CSV dari POS Santai Scale untuk analisis stok & arus kas.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: () {
                // TODO (Ahmad Jayadi): Integrasi package file_picker & HTTP MultipartRequest
              },
              icon: const Icon(Icons.folder_open),
              label: const Text('Pilih File CSV'),
            ),
          ],
        ),
      ),
    );
  }
}

// 2. SKELETON HALAMAN DASBOR ANALITIK & PREDIKSI STOK
class DashboardSkeletonPage extends StatelessWidget {
  const DashboardSkeletonPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.insights, size: 64, color: Colors.brown),
            SizedBox(height: 16),
            Text(
              'Dasbor Analitik & Prediksi Stok',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'Area widget grafik tren penjualan harian & estimasi stok 7-14 hari.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

// 3. SKELETON HALAMAN AI ADVISOR (AREA KERJA NUR AINUN)
class AIAdvisorSkeletonPage extends StatelessWidget {
  const AIAdvisorSkeletonPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.auto_awesome, size: 64, color: Colors.brown),
            SizedBox(height: 16),
            Text(
              'AI Advisor Perencanaan Belanja',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'Rekomendasi jadwal & anggaran belanja mingguan berbasis Gemini API.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}