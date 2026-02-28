import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/providers/app_provider.dart';
import '../../widgets/common/widgets.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().fetchAnalytics();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    final data = provider.analyticsData;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analíticas'),
        actions: [
          IconButton(
            onPressed: () => context.read<AppProvider>().fetchAnalytics(),
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: data == null
          ? const ShimmerList(count: 3)
          : RefreshIndicator(
              onRefresh: () => context.read<AppProvider>().fetchAnalytics(),
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── Total stats ────────────────────────────────────────
                    Row(
                      children: [
                        Expanded(
                          child: StatCard(
                            label: 'Total vistas',
                            value: '${data['total'] ?? 0}',
                            icon: Icons.visibility_rounded,
                            color: AppTheme.primary,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: StatCard(
                            label: 'Hoy',
                            value: '${data['today'] ?? 0}',
                            icon: Icons.today_rounded,
                            color: AppTheme.success,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    StatCard(
                      label: 'Este mes',
                      value: '${data['this_month'] ?? 0}',
                      icon: Icons.calendar_month_rounded,
                      color: AppTheme.info,
                    ),
                    const SizedBox(height: 24),
                    // ── Per Card ───────────────────────────────────────────
                    const Text(
                      'Vistas por tarjeta',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF111827),
                      ),
                    ),
                    const SizedBox(height: 12),
                    ...(data['per_card'] as List? ?? []).map((card) {
                      final total = card['total'] as int? ?? 0;
                      final today = card['today'] as int? ?? 0;
                      final maxVal = ((data['per_card'] as List)
                                  .map((c) => c['total'] as int? ?? 0)
                                  .fold(0, (a, b) => a > b ? a : b))
                              .toDouble();

                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFF3F4F6)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    card['card_name'] ?? 'Tarjeta',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 15,
                                    ),
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '$total total',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: AppTheme.primary,
                                        fontSize: 16,
                                      ),
                                    ),
                                    Text(
                                      '$today hoy',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: Color(0xFF9CA3AF),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: maxVal > 0 ? total / maxVal : 0,
                                backgroundColor:
                                    AppTheme.primary.withOpacity(0.1),
                                valueColor: const AlwaysStoppedAnimation(
                                    AppTheme.primary),
                                minHeight: 8,
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
    );
  }
}
