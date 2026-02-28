import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/providers/auth_provider.dart';
import '../../../data/providers/app_provider.dart';
import '../../../data/models/models.dart';
import '../../widgets/common/widgets.dart';
import '../cards/cards_list_screen.dart';
import '../appointments/appointments_screen.dart';
import '../tickets/tickets_screen.dart';
import '../profile/profile_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  final _screens = const [
    _HomeTab(),
    CardsListScreen(),
    AppointmentsScreen(),
    TicketsScreen(),
    ProfileScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().fetchDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded),
            label: 'Inicio',
          ),
          const NavigationDestination(
            icon: Icon(Icons.credit_card_outlined),
            selectedIcon: Icon(Icons.credit_card_rounded),
            label: 'Tarjetas',
          ),
          const NavigationDestination(
            icon: Icon(Icons.calendar_today_outlined),
            selectedIcon: Icon(Icons.calendar_today_rounded),
            label: 'Citas',
          ),
          if (user?.hasTicketSystem ?? false)
            const NavigationDestination(
              icon: Icon(Icons.queue_outlined),
              selectedIcon: Icon(Icons.queue_rounded),
              label: 'Turnos',
            )
          else
            const NavigationDestination(
              icon: Icon(Icons.queue_outlined),
              selectedIcon: Icon(Icons.queue_rounded),
              label: 'Turnos',
            ),
          const NavigationDestination(
            icon: Icon(Icons.person_outline_rounded),
            selectedIcon: Icon(Icons.person_rounded),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}

// ── Home Tab ──────────────────────────────────────────────────────────────

class _HomeTab extends StatefulWidget {
  const _HomeTab();

  @override
  State<_HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<_HomeTab> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().fetchDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    final user = context.watch<AuthProvider>().user;
    final dashboard = provider.dashboard;

    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      body: RefreshIndicator(
        onRefresh: () => context.read<AppProvider>().fetchDashboard(),
        child: CustomScrollView(
          slivers: [
            // ── App Bar ────────────────────────────────────────────────
            SliverAppBar(
              expandedHeight: 120,
              pinned: true,
              backgroundColor: Colors.white,
              surfaceTintColor: Colors.transparent,
              flexibleSpace: FlexibleSpaceBar(
                background: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [AppTheme.primary, AppTheme.secondary],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Text(
                        'Hola, ${user?.email.split('@')[0] ?? 'Usuario'} 👋',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const Text(
                        'Panel de control',
                        style: TextStyle(color: Colors.white70, fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            if (provider.loadingDashboard && dashboard == null)
              const SliverFillRemaining(
                child: ShimmerList(count: 4, itemHeight: 100),
              )
            else if (provider.error != null && dashboard == null)
              SliverFillRemaining(
                child: ErrorState(
                  message: provider.error!,
                  onRetry: () => context.read<AppProvider>().fetchDashboard(),
                ),
              )
            else ...[
              // ── Stats Grid ────────────────────────────────────────────
              SliverPadding(
                padding: const EdgeInsets.all(16),
                sliver: SliverGrid(
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.4,
                  ),
                  delegate: SliverChildListDelegate([
                    StatCard(
                      label: 'Tarjetas',
                      value: '${dashboard?.cardsCount ?? 0}/${dashboard?.maxCards ?? 1}',
                      icon: Icons.credit_card_rounded,
                      color: AppTheme.primary,
                    ),
                    StatCard(
                      label: 'Vistas hoy',
                      value: '${dashboard?.viewsToday ?? 0}',
                      icon: Icons.visibility_rounded,
                      color: AppTheme.info,
                    ),
                    StatCard(
                      label: 'Citas pendientes',
                      value: '${dashboard?.pendingAppointments ?? 0}',
                      icon: Icons.calendar_today_rounded,
                      color: AppTheme.warning,
                    ),
                    if (dashboard?.ticketStats != null)
                      StatCard(
                        label: 'Turnos en espera',
                        value: '${dashboard!.ticketStats!['waiting'] ?? 0}',
                        icon: Icons.queue_rounded,
                        color: AppTheme.secondary,
                      )
                    else
                      StatCard(
                        label: 'Servicios activos',
                        value: '${dashboard?.cards.fold<int>(0, (s, c) => s + c.servicesCount) ?? 0}',
                        icon: Icons.star_rounded,
                        color: AppTheme.accent,
                      ),
                  ]),
                ),
              ),

              // ── My Cards ──────────────────────────────────────────────
              if (dashboard != null && dashboard.cards.isNotEmpty) ...[
                const SliverToBoxAdapter(
                  child: SectionHeader(title: 'Mis tarjetas'),
                ),
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (ctx, i) => _CardTile(card: dashboard.cards[i]),
                      childCount: dashboard.cards.length,
                    ),
                  ),
                ),
              ],

              // ── Recent Appointments ───────────────────────────────────
              if (dashboard != null && dashboard.recentAppointments.isNotEmpty) ...[
                const SliverToBoxAdapter(
                  child: SectionHeader(
                    title: 'Próximas citas',
                  ),
                ),
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (ctx, i) =>
                          _AppointmentTile(apt: dashboard.recentAppointments[i]),
                      childCount: dashboard.recentAppointments.length,
                    ),
                  ),
                ),
              ],

              const SliverToBoxAdapter(child: SizedBox(height: 32)),
            ],
          ],
        ),
      ),
    );
  }
}

class _CardTile extends StatelessWidget {
  final CardModel card;
  const _CardTile({required this.card});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFF3F4F6)),
      ),
      child: Row(
        children: [
          UserAvatar(
            name: card.name,
            imageUrl: card.avatarUrl != null
                ? 'http://10.0.2.2:5000${card.avatarUrl}'
                : null,
            radius: 26,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  card.name,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                    color: Color(0xFF111827),
                  ),
                ),
                if (card.jobTitle != null)
                  Text(
                    card.jobTitle!,
                    style: const TextStyle(
                        fontSize: 13, color: Color(0xFF6B7280)),
                  ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: card.isPublic
                  ? AppTheme.success.withOpacity(0.1)
                  : Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              card.isPublic ? 'Publicada' : 'Borrador',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: card.isPublic ? AppTheme.success : Colors.grey,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AppointmentTile extends StatelessWidget {
  final AppointmentModel apt;
  const _AppointmentTile({required this.apt});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFF3F4F6)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppTheme.statusColor(apt.status).withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              Icons.calendar_today_rounded,
              color: AppTheme.statusColor(apt.status),
              size: 18,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  apt.customerName,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                    color: Color(0xFF111827),
                  ),
                ),
                Text(
                  '${apt.serviceName ?? "Servicio"} • ${apt.appointmentDate ?? "-"} ${apt.appointmentTime ?? ""}',
                  style: const TextStyle(
                      fontSize: 12, color: Color(0xFF6B7280)),
                ),
              ],
            ),
          ),
          StatusBadge(status: apt.status),
        ],
      ),
    );
  }
}
