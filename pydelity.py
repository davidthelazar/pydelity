from enum import Enum
import csv
# import retirement as re

def getMonthlyRate(annualRate):
    return ((1+annualRate)^(1/12)) - 1

class accountType(Enum):
    HSA = 1
    TRADITIONAL401K = 2
    ROTH401K = 2
    TRADITIONALIRA = 3
    ROTHIRA = 4
    BROKERAGE = 5 
    
class paycheck:
    gross = 0
    net = 0
    withholding = {}
    preTaxBenefits = {}
    postTaxBenefits = {}
    preTaxInvestments = {}
    postTaxInvestments = {}  
    
    def printout(this):
        print('Gross pay: $'+"{:.2f}".format(this.gross))
        print('----------------------------')
        print('Pre-tax Benefits:')
        for ben in this.preTaxBenefits.keys():
            print(ben+': $' + "{:.2f}".format(this.preTaxBenefits[ben]))
        print('----------------------------')    
        print('Post-tax Benefits:')
        for ben in this.postTaxBenefits.keys():
            print(ben+': $' + "{:.2f}".format(this.postTaxBenefits[ben]))
        print('----------------------------')    
        print('Pre-tax Investments:')
        for inv in this.preTaxInvestments.keys():
            print(inv.name+': $' + "{:.2f}".format(this.preTaxInvestments[inv]))
        print('----------------------------')
        print('Post-tax Investments:')
        for inv in this.postTaxInvestments.keys():
            print(inv.name+': $' + "{:.2f}".format(this.postTaxInvestments[inv]))
        print('----------------------------')    
        print('Tax Withholding:')
        print('Fed Withholding: $'+"{:.2f}".format(this.withholding['federal']))
        print('State Withholding: $'+"{:.2f}".format(this.withholding['state']))
        print('FICA Withholding: $'+"{:.2f}".format(this.withholding['medicare']))
        print('Social Security Withholding: $'+"{:.2f}".format(this.withholding['socialsecurity']))                
        print('----------------------------')
        print('Net Pay: $' + "{:.2f}".format(this.net))
        
class taxBracket:
    thresholds = [] #Start at zero typically; for each rate, this is the minimum amount at which that rate starts
    rates = []
    stdDeduction = 0
    credits = 0
    # maxTax = 1000000000 #basically Inf
    
    def __init__(this,t=[],r=[],d=0):
        this.thresholds = t
        this.rates = r
        this.stdDeduction = d
    
    def getTax(this,gross):
        for idx in range(len(this.rates)):
            if idx == 0:
                marginalRates = [this.rates[idx]]
            else:
                marginalRates.append(this.rates[idx]-this.rates[idx-1])

        taxableIncome = gross-this.stdDeduction
        if taxableIncome<=0:
            return 0
        marginalTax = [r*max(0,taxableIncome-t) for t,r in zip(this.thresholds,marginalRates)]
        # for (idx,threshold) in enumerate(this.thresholds):
        #     marginalIncome = max(0,taxableIncome-threshold)
        #     marginalTax.append(marginalIncome*marginalRates[idx])
        totalTax = sum(marginalTax) - this.credits
        # if totalTax>maxTax:
        #     totalTax = maxTax
        # effectiveRate = totalTax/taxableIncome
        return totalTax#,effectiveRate
    def getTaxForRange(this,incomeRange):
        #untested
         taxes = [this.getTax(i) for i in incomeRange]
         return taxes[1]-taxes[0]
    def getTaxMonthly(this,annualGross):
        return this.getTax(annualGross)/12

    @staticmethod
    def getBracketsForYear(year):

        if year == 2021:
            fParams = ([0,19900,81050,172750,329850,418850,628300],[.1,.12,.22,.24,.32,.35,.37],25100)
            sParams = ([0,1000,6000],[.02,.04,.05],0)
            mParams = ([0,200000],[.0145,.0235],0)
            ssParams = ([0,142800],[.062,0],0)
        if year == 2022:
            fParams = ([0,20500,83550,178151,340100,431900,647850],[.1,.12,.22,.24,.32,.35,.37],25900)
            sParams = ([0,1000,6000],[.02,.04,.05],0)
            mParams = ([0,200000],[.0145,.0235],0)
            ssParams = ([0,142800],[.062,0],0)
        
        return {'federal':taxBracket(*fParams),'state':taxBracket(*sParams),'medicare':taxBracket(*mParams),'socialsecurity':taxBracket(*ssParams)}
        
             
class w4:
    credits = 0
    deductions = 0 #above standard
    
class career:
    salary = 0 #annual #do we want this?
    brackets = {}
    # federalBracket = re.taxBracket()
    # stateBracket = re.taxBracket()
    # medicareBracket = re.taxBracket()
    # ssBracket = re.taxBracket()
    preTaxBenefits = {} #monthly
    postTaxBenefits = {} #monthly
    #investments are the amount contributed from pay. The account itself will determine match, etc 
    preTaxInvestments = {} #monthly
    postTaxInvestments = {} #monthly
    federalW4 = w4()
    #
    # def getTotalTax(this):
    
    def getPaycheck(this):
        pc = paycheck()
        taxable = this.getTaxableIncome()
        medicareTaxable = this.getMedicareTaxableIncome()
        stateTaxable = this.getStateTaxableIncome()
        pc.gross = this.salary/12
        pc.withholding['federal'] = (this.brackets['federal'].getTax(taxable)-this.federalW4.credits)/12
        pc.withholding['state'] = this.brackets['state'].getTax(stateTaxable)/12
        pc.withholding['medicare'] = this.brackets['medicare'].getTax(medicareTaxable)/12
        pc.withholding['socialsecurity'] = this.brackets['socialsecurity'].getTax(medicareTaxable)/12
        pc.preTaxBenefits = this.preTaxBenefits
        pc.postTaxBenefits = this.postTaxBenefits
        pc.preTaxInvestments = this.preTaxInvestments
        pc.postTaxInvestments = this.postTaxInvestments   
        pc.net = pc.gross-pc.withholding['federal']-pc.withholding['state']-pc.withholding['medicare']-pc.withholding['socialsecurity']-sum(pc.preTaxBenefits.values())-sum(pc.postTaxBenefits.values())-sum(pc.preTaxInvestments.values())-sum(pc.postTaxInvestments.values())
        return pc

    def getCumulativePaycheck(this,nMonths):
        # for idx in range(0,nMonths):
        pc = this.getPaycheck()
        pc.gross = pc.gross*nMonths
        pc.net = pc.net*nMonths
        for w in pc.withholding:
            pc.withholding[w] = pc.withholding[w]*nMonths
        for w in pc.preTaxBenefits:
            pc.preTaxBenefits[w] = pc.preTaxBenefits[w]*nMonths
        for w in pc.postTaxBenefits:
            pc.postTaxBenefits[w] = pc.postTaxBenefits[w]*nMonths
        for w in pc.preTaxInvestments:
            pc.preTaxInvestments[w] = pc.preTaxInvestments[w]*nMonths
        for w in pc.postTaxInvestments:
            pc.postTaxInvestments[w] = pc.postTaxInvestments[w]*nMonths
        return pc
    
    def getTaxableIncome(this):
        return this.salary - 12*sum(this.preTaxBenefits.values()) - 12*sum(this.preTaxInvestments.values()) - this.federalW4.deductions
    def getMedicareTaxableIncome(this):
        #same used for social security
        return this.salary - 12*sum(this.preTaxBenefits.values())-12*this.preTaxInvestments[accountType.HSA]
    def getStateTaxableIncome(this):
        return this.getTaxableIncome() - this.brackets['federal'].getTax(this.getTaxableIncome()) - this.brackets['medicare'].getTax(this.getMedicareTaxableIncome()) - this.brackets['socialsecurity'].getTax(this.getMedicareTaxableIncome())
    def getRaise(this,frac):
        this.salary = this.salary*(1+frac)
    
class account:
    #TODO: any way to make 401k/ira limits work across trad/roth? Maybe the limits shouldn't even be part of the account, but part of the portfolio instead, and managed before a contribution is ever made
    #TODO: 
    name = ''
    # taxRateIn = 0
    # taxRateGrowth = 0
    # taxRateOut = 0
    annualMax = 1000000
    annualGrowthRate = .05
    balance = 0
    principal = 0
    # totalTax = 0
    matchRate = 0
    matchMin = 0        
    matchMax = 0
    currentYearContribution = 0
    currentYearMatch = 0
    
    type = accountType.BROKERAGE    
        
 
    def invest(this,dollars):
        overage = 0

        if dollars+currentYearContribution>this.annualMax:
            raise ValueError('The attempted contribution amount of '+str(dollars)+'to '+this.name+' exceeds the maximum contribution amount of '+str(this.annualMax))
            print('this should never print')
            
        matchDollars = dollars*this.matchRate
        if matchDollars+this.currentYearMatch>this.matchMax:
            matchDollars = this.matchMax-this.currentYearMatch
        this.currentYearMatch = this.currentYearMatch+matchDollars
        this.currentYearContribution = this.currentYearContribution + dollars
        totalDollars = dollars+matchDollars
        # tax = dollars*this.taxRateIn #nothing that matches should also have taxratein, right?
        this.balance = this.balance + totalDollars
        this.principal = this.principal+totalDollars

        # this.totalTax = this.totalTax + tax
        
        # return overage
        
    def compoundAnnual(this,years):
        growth = this.balance*(((1+this.annualGrowthRate)**years)-1)
        # tax = growth*this.taxRateGrowth
        this.balance = this.balance+growth
        # this.totalTax = this.totalTax+tax
        # return (growth,tax)

    def compoundMonthly(this,months):
        growth = this.balance*(((1+getMonthlyRate(this.annualGrowthRate))**months)-1)
        # tax = growth*this.taxRateGrowth
        this.balance = this.balance+growth
        # this.totalTax = this.totalTax+tax
        # return (growth,tax)
    
    def withdraw(this,dollars):
        #withdraws principal first for anything but roth 401k
        if dollars>this.balance:
            raise ValueError('The attempted withdrawal amount of '+str(dollars)+'from '+this.name+' exceeds the balance of '+str(this.balance))
        this.balance = this.balance-dollars
        principalAmount = 0
        if this.principal>0:
            if this.type == accountType.ROTH401K:
                pFrac = this.principal/this.balance
                principalAmount = min(pFrac*dollars,principal)
            else:
                principalAmount = min(dollars,this.principal)
            this.principal = max(this.principal-principalAmount,0)
            
        return (valueOut,principalAmount) 
        
    def getEarnings(this):
        return this.balance-this.principal
    def isPretax(this):
        return this.type in [accountType.TRADITIONAL401K,accountType.TRADITIONALIRA,accountType.HSA]
    def isSubjectToCapitalGains(this):
        return this.type == accountType.BROKERAGE
    def isTaxfree(this):
        return this.type in [accountType.ROTH401K,accountType.ROTHIRA,accountType.HSA]
    def getPenalty(this,age,amount,principalAmount):
        #10% early withdrawal penalty on whole withdrawal for traditionals, earnings for roths
        
        if age<59.5:
            if this.type in [accountType.TRADITIONAL401K,accountType.TRADITIONALIRA]:
                return amount*0.1
            elif this.type in [accountType.ROTH401K,accountType.ROTHIRA]:
                return principalAmount*0.1
        return 0
    def endYear(this):

        if this.currentYearMatch<this.matchMin:
            catchup = this.matchMin-this.currentYearMatch
            this.balance = this.balance + catchup
            this.principal = this.principal+catchup

        this.currentYearContribution = 0
        this.currentYearMatch = 0
           #would need tax bracket, current income
    # def withdrawByTarget(this,targetDollars):
    #     withdrawDollars = targetDollars/(1-this.taxRateOut)
    #     valueOut,tax = this.withdraw(withdrawDollars)
    #     return (valueOut,tax)
        
    # def calculateTaxLimitedInvestment(this,dollarsDesired,dollarsRemaining):
    #     dollarsSafe = dollarsRemaining;
    #     tax = dollarsDesired*this.taxRateIn
    #     burden = dollarsDesired+tax
    #     if burden>dollarsRemaining:
    #         dollarsSafe = dollarsTotal/(1+this.taxRateIn);
    #     return dollarsSafe
    
class portfolioLog:
    logs = []
    
    def addEntry(this,age,netWorth,tax):
        this.logs.append({'age':age,'netWorth':netWorth,'tax':tax})
    def print2csv(this,filePath = '~/retirementLog.csv'):
        with open(filePath,mode='a') as csvFile:
            csvWriter = csv.writer(csvFile, delimiter=',')
            row = ['age','netWorth','tax']
            csvWriter.writerow(row)
            
            for log in this.logs:
                row = [log['age'],log['netWorth'],log['tax']]
                csvWriter.writerow(row)
                
                     
class portfolio:
    accounts = []
    job = career()
    cash = 0
    taxableIncome = 0
    capitalGainsIncome = 0
    # priority
    incomeBracket = taxBracket()
    capitalGainsBracket = taxBracket()
    stateBracket = taxBracket()
    totalTax = 0
    annualSpending = 1
    annualIncome = 1
    age = 1
    log = portfolioLog()
    
    
    def getPaid(this): 
        1
        #TODOsort paycheck output into relevant fields here
        # pc = this.job.getPaycheck()
        # this.cash = this.cash+pc.net
        # thiz
    
    def investIn(this,accountIdx,amount):
        if amount>this.cash:
            raise ValueError('That is more money than you have')
        acct = this.accounts[accountIdx]
        acct.invest(amount)
        if acct.isPretax:
            this.taxableIncome = this.taxableIncome-amount
        this.cash = this.cash-amount    
        
    def withdrawFrom(this,accountIdx,amount):
        #early withdrawal penalty paid at time of withdrawal, but included in total tax
        #income taxes not paid until end of year
        acct = this.accounts[accountIdx]
        withdrawal,fromPrincipal = acct.withdraw(amount)
        penalty = acct.getPenalty(this.age,withdrawal,fromPrincipal)
        this.cash = this.cash+withdrawal-penalty
        #penalty included in taxes
        this.totalTax = this.totalTax+penalty 
        if not acct.isTaxFree:
            this.taxableIncome = this.taxableIncome+withdrawal
        if acct.isSubjectToCapitalGains:
            #TODO: this is treating entire withdrawal from brokerage as capital gains... but I think it should actually just be the earnings? not sure how to calculate
            this.capitalGainsIncome = this.capitalGainsIncome+withdrawal
            
    def compoundAll(this,years):
        for acct in this.accounts:
            acct.compound(years)
    
    def spend(this,amount):
        if amount>this.cash:
            raise ValueError('That is more money than you have')
                        
        this.cash = this.cash-amount
    
    def payTaxes(this):
        allTax = this.currentTaxBurden()
        this.cash = this.cash-allTax
        this.totalTax = this.totalTax+allTax
        return allTax
    
    def endYear(this):
        for acct in this.accounts:
            acct.endYear()
        taxThisYear = this.payTaxes()
        this.compoundAll(1) #be careful not to compound monthly AND anually
        this.spend(this.annualSpending)
        this.log.addEntry(age=this.age,netWorth = this.getNetWorth(),tax = taxThisYear)
    def newYear(this):
        this.taxableIncome = 0
        this.capitalGainsIncome = 0
        this.getPaid()
        this.age = this.age+1    
        
    def currentTaxBurden(this):
        incomeTax = this.incomeBracket.getTax(this.taxableIncome)
        stateTax = this.stateBracket.getTax(this.taxableIncome)
        capitalGainsTax = this.capitalGainsBracket.getTax(this.capitalGainsIncome)
        return incomeTax+stateTax+capitalGainsTax

    def investableFunds(this):
        return this.cash-this.annualSpending-this.currentTaxBurden()
 
    def getNetWorth(this):
        total = 0
        total = total+this.cash
        for account in this.accounts:
            total = total+account.balance
        
        return total
    
def testPaycheck():
    sim = career()
    sim.salary = 90000
    sim.federalW4 = w4()
    sim.federalW4.credits = 0
    sim.federalW4.deductions = 0
    #brackets here are just used for calculating withholding
    sim.brackets = taxBracket.getBracketsForYear(2021)
    # sim.federalBracket = re.taxBracket()
    # sim.federalBracket.thresholds = [0,19900,81050,172750,329850,418850,628300]
    # sim.federalBracket.rates = [.1,.12,.22,.24,.32,.35,.37]
    # sim.federalBracket.stdDeduction = 25100
    # sim.stateBracket = re.taxBracket()
    # sim.stateBracket.thresholds = [0,1000,6000]
    # sim.stateBracket.rates = [.02,.04,.05]
    # sim.medicareBracket = re.taxBracket()
    # sim.medicareBracket.thresholds = [0,200000]
    # sim.medicareBracket.rates = [.0145,.0235]
    # sim.ssBracket = re.taxBracket()
    # sim.ssBracket.thresholds = [0,142800]
    # sim.ssBracket.rates = [.062,0]
    sim.preTaxBenefits = {"dental":39.44,"medical":318.81,"vision":33.83}
    sim.postTaxBenefits = {"life":14}
    sim.preTaxInvestments = {accountType.HSA:300,accountType.TRADITIONAL401K:1625}
    return sim.getPaycheck(),sim.getCumulativePaycheck(12)