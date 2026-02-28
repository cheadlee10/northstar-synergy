/**
 * John's Revenue Mock Data Factory
 * Generates realistic mock data for jobs, invoices, and collections
 */

const { v4: uuidv4 } = require('uuid');

class JohnMockDataFactory {
  /**
   * Generate a job/contract
   */
  static generateJob(overrides = {}) {
    const value = Math.random() * 50000 + 5000; // $5K - $55K
    
    return {
      id: uuidv4(),
      clientName: `Client-${Math.floor(Math.random() * 1000)}`,
      description: 'Business Development Project',
      value: parseFloat(value.toFixed(2)),
      status: ['pending', 'in-progress', 'completed'][Math.floor(Math.random() * 3)],
      startDate: new Date(Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000),
      endDate: new Date(Date.now() + Math.random() * 90 * 24 * 60 * 60 * 1000),
      invoiced: false,
      collected: false,
      ...overrides
    };
  }

  /**
   * Generate multiple jobs
   */
  static generateJobs(count = 5, overrides = {}) {
    return Array.from({ length: count }, () => 
      this.generateJob(overrides)
    );
  }

  /**
   * Generate an invoice
   */
  static generateInvoice(overrides = {}) {
    const amount = Math.random() * 50000 + 5000;
    const invoiceNumber = `INV-${Math.floor(Math.random() * 100000)}`;
    
    return {
      id: uuidv4(),
      invoiceNumber,
      clientName: `Client-${Math.floor(Math.random() * 1000)}`,
      amount: parseFloat(amount.toFixed(2)),
      issuedDate: new Date(Date.now() - Math.random() * 60 * 24 * 60 * 60 * 1000),
      dueDate: new Date(Date.now() + Math.random() * 30 * 24 * 60 * 60 * 1000),
      status: ['draft', 'sent', 'viewed', 'paid'][Math.floor(Math.random() * 4)],
      paymentTerms: '30 days',
      paidDate: null,
      ...overrides
    };
  }

  /**
   * Generate multiple invoices
   */
  static generateInvoices(count = 10, overrides = {}) {
    return Array.from({ length: count }, () => 
      this.generateInvoice(overrides)
    );
  }

  /**
   * Generate a payment collection
   */
  static generateCollection(overrides = {}) {
    const amount = Math.random() * 50000 + 5000;
    
    return {
      id: uuidv4(),
      invoiceNumber: `INV-${Math.floor(Math.random() * 100000)}`,
      clientName: `Client-${Math.floor(Math.random() * 1000)}`,
      amount: parseFloat(amount.toFixed(2)),
      collectedDate: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
      paymentMethod: ['bank', 'card', 'wire', 'check'][Math.floor(Math.random() * 4)],
      status: 'collected',
      ...overrides
    };
  }

  /**
   * Generate multiple collections
   */
  static generateCollections(count = 8, overrides = {}) {
    return Array.from({ length: count }, () => 
      this.generateCollection(overrides)
    );
  }

  /**
   * Generate complete John's revenue snapshot
   */
  static generateRevenueSnapshot(overrides = {}) {
    const jobs = this.generateJobs(Math.floor(Math.random() * 3) + 2);
    const invoices = this.generateInvoices(Math.floor(Math.random() * 5) + 3);
    const collections = this.generateCollections(Math.floor(Math.random() * 4) + 2);

    // Calculate totals
    const totalInvoiced = invoices.reduce((sum, inv) => sum + inv.amount, 0);
    const totalCollected = collections.reduce((sum, col) => sum + col.amount, 0);
    const outstanding = totalInvoiced - totalCollected;

    return {
      jobs: {
        total: jobs.length,
        data: jobs
      },
      invoices: {
        total: invoices.length,
        totalAmount: parseFloat(totalInvoiced.toFixed(2)),
        data: invoices
      },
      collections: {
        total: collections.length,
        totalAmount: parseFloat(totalCollected.toFixed(2)),
        data: collections
      },
      summary: {
        invoiced: parseFloat(totalInvoiced.toFixed(2)),
        collected: parseFloat(totalCollected.toFixed(2)),
        outstanding: parseFloat(outstanding.toFixed(2)),
        collectionRate: parseFloat(((totalCollected / totalInvoiced) * 100).toFixed(2))
      },
      timestamp: new Date().toISOString(),
      ...overrides
    };
  }

  /**
   * Scenario: High collection rate
   */
  static generateHighCollectionScenario() {
    const invoices = [
      { invoiceNumber: 'INV-001', amount: 25000, status: 'paid' },
      { invoiceNumber: 'INV-002', amount: 15000, status: 'paid' },
      { invoiceNumber: 'INV-003', amount: 20000, status: 'paid' },
      { invoiceNumber: 'INV-004', amount: 30000, status: 'sent' }
    ];

    const totalInvoiced = invoices.reduce((sum, inv) => sum + inv.amount, 0);
    const collections = [
      { invoiceNumber: 'INV-001', amount: 25000, paymentMethod: 'wire' },
      { invoiceNumber: 'INV-002', amount: 15000, paymentMethod: 'bank' },
      { invoiceNumber: 'INV-003', amount: 20000, paymentMethod: 'card' }
    ];
    const totalCollected = collections.reduce((sum, col) => sum + col.amount, 0);

    return {
      invoiced: totalInvoiced,
      collected: totalCollected,
      outstanding: totalInvoiced - totalCollected,
      collectionRate: (totalCollected / totalInvoiced) * 100,
      scenario: 'high_collection'
    };
  }

  /**
   * Scenario: Low collection rate
   */
  static generateLowCollectionScenario() {
    const invoices = [
      { invoiceNumber: 'INV-001', amount: 25000, status: 'sent' },
      { invoiceNumber: 'INV-002', amount: 15000, status: 'sent' },
      { invoiceNumber: 'INV-003', amount: 20000, status: 'viewed' },
      { invoiceNumber: 'INV-004', amount: 30000, status: 'viewed' }
    ];

    const totalInvoiced = invoices.reduce((sum, inv) => sum + inv.amount, 0);
    const collections = [
      { invoiceNumber: 'INV-001', amount: 25000, paymentMethod: 'wire' }
    ];
    const totalCollected = collections.reduce((sum, col) => sum + col.amount, 0);

    return {
      invoiced: totalInvoiced,
      collected: totalCollected,
      outstanding: totalInvoiced - totalCollected,
      collectionRate: (totalCollected / totalInvoiced) * 100,
      scenario: 'low_collection'
    };
  }

  /**
   * Scenario: Perfect collection
   */
  static generatePerfectCollectionScenario() {
    const invoices = [
      { invoiceNumber: 'INV-001', amount: 25000, status: 'paid' },
      { invoiceNumber: 'INV-002', amount: 15000, status: 'paid' },
      { invoiceNumber: 'INV-003', amount: 20000, status: 'paid' }
    ];

    const totalInvoiced = invoices.reduce((sum, inv) => sum + inv.amount, 0);
    const collections = invoices.map(inv => ({
      invoiceNumber: inv.invoiceNumber,
      amount: inv.amount,
      paymentMethod: 'wire'
    }));
    const totalCollected = collections.reduce((sum, col) => sum + col.amount, 0);

    return {
      invoiced: totalInvoiced,
      collected: totalCollected,
      outstanding: 0,
      collectionRate: 100,
      scenario: 'perfect_collection'
    };
  }

  /**
   * Generate revenue forecast (next 90 days)
   */
  static generateRevenueForecast(days = 90) {
    const forecast = [];
    const today = new Date();

    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + i);
      
      // More likely to have revenue on business days
      const isWeekend = date.getDay() === 0 || date.getDay() === 6;
      const projectedRevenue = isWeekend ? 0 : Math.random() * 30000;

      forecast.push({
        date: date.toISOString().split('T')[0],
        projectedInvoicing: parseFloat(projectedRevenue.toFixed(2)),
        confidence: (Math.random() * 40 + 60).toFixed(0) // 60-100%
      });
    }

    return {
      period: '90 days',
      startDate: today.toISOString().split('T')[0],
      forecast,
      totalProjected: parseFloat(
        forecast.reduce((sum, day) => sum + day.projectedInvoicing, 0).toFixed(2)
      )
    };
  }

  /**
   * Generate payment aging report
   */
  static generatePaymentAging() {
    return {
      current: {
        count: Math.floor(Math.random() * 5) + 2,
        amount: parseFloat((Math.random() * 30000 + 10000).toFixed(2)),
        daysOverdue: 0
      },
      '1-30days': {
        count: Math.floor(Math.random() * 4) + 1,
        amount: parseFloat((Math.random() * 25000 + 5000).toFixed(2)),
        daysOverdue: 15
      },
      '31-60days': {
        count: Math.floor(Math.random() * 3),
        amount: parseFloat((Math.random() * 20000).toFixed(2)),
        daysOverdue: 45
      },
      '61+days': {
        count: Math.floor(Math.random() * 2),
        amount: parseFloat((Math.random() * 15000).toFixed(2)),
        daysOverdue: 75
      }
    };
  }
}

module.exports = { JohnMockDataFactory };
