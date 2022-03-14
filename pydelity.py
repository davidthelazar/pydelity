from enum import Enum
import csv
#TODO: should portfolio/career know the current year? if so, does 
#taxBracket class need to have a failover for unhandled years? 
#and if so, should it try to predict brackets or just keep the most 
#recent? 
#TODO: include inflation in some sense
#TODO: Everything tax related assumes Married Filing Joint. Should I fix that?
#TODO: AGI method
#TODO: MAGI method
#TODO: check income limits for Traditional IRA, Roth IRA, spousal IRA
#TODO: W2 Generator
#TODO: accountRules structure, for consolidated place to define all rules (instead of "if tradIRA"-type checks tucked away here and there)
#---------------------------------------
#helper functions
def getMonthlyRate(annualRate):
    return ((1+annualRate)^(1/12)) - 1
#---------------------------------------
#enumerations
class accountType(Enum):
    HSA = 0
    TRADITIONAL401K = 1
    ROTH401K = 2
    TRADITIONALIRA = 3
    ROTHIRA = 4
    BROKERAGE = 5 
    FIVETWENTYNINE = 6

class taxType(Enum):
    #currently unused, but they tell me online I shouldn't use strings for this shit
    FEDERAL = 1
    STATE = 2
    MEDICARE = 3
    SOCIALSECURITY = 4
    CAPITALGAINS = 5
class filingStatus(Enum):
    #currently unused, but they tell me online I shouldn't use strings for this shit
    SINGLE = 1
    MARRIEDFILINGSEPARATE = 2
    MARRIEDFILINGJOINT = 3
    HEADOFHOUSEHOLD = 4    
#---------------------------------------
#taxes
class taxBracket:

    def __init__(this,t=[],r=[],d=0,c=0):
        this.thresholds = t
        this.rates = r
        this.stdDeduction = d
        this.credits = c #uh, not sure on this
    
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
        
        totalTax = sum(marginalTax) - this.credits
        
        return totalTax
        
    def getTaxForRange(this,incomeRange):
        #untested
         taxes = [this.getTax(i) for i in incomeRange]
         return taxes[1]-taxes[0]
         
    def getTaxMonthly(this,annualGross):
        return this.getTax(annualGross)/12

    @staticmethod
    def getBracketsForYear(year):
        #TODO: These are all MFJ, should I add others? if so, how? 
        #TODO: Should we be grabbing this from a file or something?
        #TODO: in future, use some inflation factor?
        if year == 2021:
            fParams = ([0,19900,81050,172750,329850,418850,628300],[.1,.12,.22,.24,.32,.35,.37],25100)
            sParams = ([0,1000,6000],[.02,.04,.05],0)
            mParams = ([0,200000],[.0145,.0235],0)
            ssParams = ([0,142800],[.062,0],0)
            cgParams = ([0,80800,501600],[0,.15,.20],0)
        elif year >= 2022:
            fParams = ([0,20500,83550,178151,340100,431900,647850],[.1,.12,.22,.24,.32,.35,.37],25900)
            sParams = ([0,1000,6000],[.02,.04,.05],0)
            mParams = ([0,200000],[.0145,.0235],0)
            ssParams = ([0,142800],[.062,0],0)
            cgParams = ([0,83350,517200],[0,.15,.20],0)
        # else:
        #     #currently same as 2022 for all years >2022
        #     fParams = ([0,20500,83550,178151,340100,431900,647850],[.1,.12,.22,.24,.32,.35,.37],25900)
        #     sParams = ([0,1000,6000],[.02,.04,.05],0)
        #     mParams = ([0,200000],[.0145,.0235],0)
        #     ssParams = ([0,142800],[.062,0],0)
        #     cgParams = ([0,83350,517200],[0,.15,.20],0)
            
        return {'federal':taxBracket(*fParams),'state':taxBracket(*sParams),'medicare':taxBracket(*mParams),'socialsecurity':taxBracket(*ssParams),'capitalgains':taxBracket(*cgParams)}            
#---------------------------------------
#paycheck/withholding/w4 stuff  
class paycheck:
    def __init__(this):
        #just set defaults for now
        this.gross = 0
        this.net = 0
        this.withholding = {}
        this.preTaxBenefits = {}
        this.postTaxBenefits = {}
        this.preTaxInvestments = {}
        this.postTaxInvestments = {}  
        this.taxable = {}
    
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
             
class w4:
    def __init__(this,c=0,d=0,ew=0): #temp names
        this.credits = c            #CTC, EV, etc
        this.deductions = d         #above standard... like IRA, etc
        this.extraWithholding = ew
    
class career:
    #TODO: generate W2
    #TODO: State w4
    def __init__(this):
        #just set defaults for now
        this.salary = 0 
        this.brackets = {}
        this.preTaxBenefits = {} #monthly
        this.postTaxBenefits = {} #monthly
        #investments are the amount contributed from pay. The account itself will determine match, etc -----right? should it?
        this.preTaxInvestments = {} #monthly
        this.postTaxInvestments = {} #monthly
        this.federalW4 = w4()
    
    def getPaycheck(this):
        pc = paycheck()
        pc.taxable['federal'] = this.getFederalTaxableIncome()
        pc.taxable['medicare'] = this.getMedicareTaxableIncome()
        pc.taxable['state'] = this.getStateTaxableIncome()
        pc.gross = this.salary/12
        pc.withholding['federal'] = (this.brackets['federal'].getTax(pc.taxable['federal']-this.federalW4.deductions)-this.federalW4.credits+this.federalW4.extraWithholding)/12 #use tax burden with w4 deductions, then subtract w4 credits and add w4 exra WH
        pc.withholding['state'] = this.brackets['state'].getTax(pc.taxable['state'])/12
        pc.withholding['medicare'] = this.brackets['medicare'].getTax(pc.taxable['medicare'])/12
        pc.withholding['socialsecurity'] = this.brackets['socialsecurity'].getTax(pc.taxable['medicare'])/12
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
    
    def getFederalTaxableIncome(this):
        return this.salary - 12*sum(this.preTaxBenefits.values()) - 12*sum(this.preTaxInvestments.values())
    def getMedicareTaxableIncome(this):
        #same used for social security
        return this.salary - 12*sum(this.preTaxBenefits.values())-12*this.preTaxInvestments[accountType.HSA]
    def getStateTaxableIncome(this):
        return this.getFederalTaxableIncome() - this.brackets['federal'].getTax(this.getFederalTaxableIncome()) - this.brackets['medicare'].getTax(this.getMedicareTaxableIncome()) - this.brackets['socialsecurity'].getTax(this.getMedicareTaxableIncome())
    def getRaise(this,frac):
        this.salary = this.salary*(1+frac)
#---------------------------------------
#retirement accounts    
class account:
    #TODO: any way to make 401k/ira limits work across trad/roth? Maybe the limits shouldn't even be part of the account, but part of the portfolio instead, and managed before a contribution is ever made
        
    def __init__(this):
        this.name = ''
        this.annualMax = 1000000
        this.annualGrowthRate = .05
        this.balance = 0
        this.principal = 0
        this.matchRate = 0
        this.matchMin = 0        
        this.matchMax = 0
        this.currentYearContribution = 0
        this.currentYearMatch = 0
        this.incomeLimit = 999999999
    
        this.type = accountType.BROKERAGE    
        
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

        this.balance = this.balance + totalDollars
        this.principal = this.principal+totalDollars
        
    def compoundAnnual(this,years):
        growth = this.balance*(((1+this.annualGrowthRate)**years)-1)
        this.balance = this.balance+growth

    def compoundMonthly(this,months):
        growth = this.balance*(((1+getMonthlyRate(this.annualGrowthRate))**months)-1)
        this.balance = this.balance+growth
 
    def withdraw(this,dollars):
        #withdraws principal first for anything but roth 401k
        if dollars>this.balance:
            raise ValueError('The attempted withdrawal amount of '+str(dollars)+'from '+this.name+' exceeds the balance of '+str(this.balance))
        this.balance = this.balance-dollars
        principalAmount = 0
        if this.principal>0:
            if this.type in [accountType.ROTH401K,accountType.FIVETWENTYNINE]:
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
    def isPreStateTax(this):
        return this.type in [accountType.FIVETWENTYNINE,accountType.TRADITIONAL401K,accountType.TRADITIONALIRA,accountType.HSA]
    def isStateTaxFree(this):        
        return this.type in [accountType.FIVETWENTYNINE,accountType.ROTH401K,accountType.ROTHIRA,accountType.HSA]
    def getEarlyWithdrawalPenalty(this,age,amount,principalAmount):
        #10% early withdrawal penalty on whole withdrawal for traditionals, earnings for roths
        #TODO: doesn't work for 529
        if age<59.5:
            if this.type in [accountType.TRADITIONAL401K,accountType.TRADITIONALIRA]:
                return amount*0.1
            elif this.type in [accountType.ROTH401K,accountType.ROTHIRA]:
                return (amount-principalAmount)*0.1
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
#---------------------------------------
#portfolio management
    
class portfolioLog:
    #TODO: Really need to think about what the most useful info in each row would be
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
  
# class annual
                
class portfolio:

   
    def __init__(this,year=2021): 
        # this.accounts = {}
        this.job = career()
        this.cash = 0
        # this.taxable = {}
        # this.brackets = {}
        this.totalTax = 0
        this.annualSpending = 1
        this.annualIncome = 1
        this.age = 1
        this.year = 2021
        this.month = 0 #not used yet
        this.log = portfolioLog()
        # this.withholding = {}
        
        this.accounts = {accountType.HSA:0,accountType.TRADITIONAL401K:0,accountType.ROTH401K:0,accountType.TRADITIONALIRA:0,accountType.ROTHIRA:0,accountType.BROKERAGE:0,accountType.FIVETWENTYNINE:0}
        this.taxable = {'federal':0,'state':0,'medicare':0,'socialsecurity':0,'capitalgains':0}
        this.brackets = taxBracket.getBracketsForYear(year)
        this.withholding = {'federal':0,'state':0,'medicare':0,'socialsecurity':0}
        
    def getPaid(this): 
        
        pc = this.job.getPaycheck()
        
        this.cash = this.cash+pc.net
        
        for key in this.taxable.keys():
            if key in pc.taxable.keys():
                this.taxable[key] = this.taxable[key]+pc.taxable[key]
        for key in this.withholding.keys():
            if key in pc.withholding.keys():
                this.withholding[key] = this.withholding[key]+pc.withholding[key]
        #note the next two loop over what's in the paycheck instead of what's here        
        for key in pc.preTaxInvestments.keys():
            if key in this.accounts.keys():
                this.accounts[key].invest(pc.preTaxInvestments[key])
        for key in pc.postTaxInvestments.keys():
            if key in this.accounts.keys():
                this.accounts[key].invest(pc.postTaxInvestments[key])
        
    def contributeTo(this,acctType,amount):
        if amount>this.cash:
            raise ValueError('That is more money than you have')
        acct = this.accounts[acctType]
        acct.invest(amount)
        if acct.isPretax:
            this.taxable['federal'] = this.taxable['federal']-amount
        if acct.isPreStateTax:    
            this.taxable['state'] = this.taxable['state']-amount
        this.cash = this.cash-amount    
        
    def withdrawFrom(this,acctType,amount):
        #early withdrawal penalty paid at time of withdrawal, but included in total tax
        #income taxes not paid until end of year
        acct = this.accounts[acctType]
        withdrawal,fromPrincipal = acct.withdraw(amount)
        penalty = acct.getEarlyWithdrawalPenalty(this.age,withdrawal,fromPrincipal)
        this.cash = this.cash+withdrawal-penalty
        #penalty included in taxes
        this.totalTax = this.totalTax+penalty 
        if not acct.isTaxFree:
            this.taxableIncome = this.taxableIncome+withdrawal
        if acct.isSubjectToCapitalGains:
            #TODO: this is treating entire withdrawal from brokerage as capital gains... but I think it should actually just be the earnings? not sure how to calculate
            this.capitalGainsIncome = this.capitalGainsIncome+withdrawal
            
    def compoundAllAnnual(this,years):
        for acct in this.accounts.values():
            acct.compoundAnnual(years)
            
    def compoundAllMonthly(this,months):
        for acct in this.accounts.values():
            acct.compoundMonthly(months)
            
    def spend(this,amount):
        if amount>this.cash:
            raise ValueError('That is more money than you have')
                        
        this.cash = this.cash-amount
    
    def payTaxes(this):
        federalBurden,stateBurden,capitalGainsOwed = this.currentTaxBurden()
        federalOwed = federalBurden - this.federalWithheld
        stateOwed = stateBurden - this.stateWithheld        
        allTax = federalBurden + stateBurden + capitalGainsOwed
        this.cash = this.cash-federalOwed-stateOwed-capitalGainsOwed
        this.totalTax = this.totalTax+allTax
        return allTax
    
    def endYear(this):
        for acct in this.accounts.values():
            acct.endYear()
        taxThisYear = this.payTaxes()
        # this.compoundAll(1) #be careful not to compound monthly AND anually
        this.spend(this.annualSpending)
        this.log.addEntry(age=this.age,netWorth = this.getNetWorth(),tax = taxThisYear)
    def newYear(this):
        this.age = this.age+1    
        this.year = this.year+1
                
        this.taxableIncome = 0
        this.capitalGainsIncome = 0
        # this.getPaid()
    
        this.taxable = {'federal':0,'state':0,'medicare':0,'socialsecurity':0,'capitalgains':0}
        this.brackets = taxBracket.getBracketsForYear(year)
        this.withholding = {'federal':0,'state':0,'medicare':0,'socialsecurity':0}
    
    def currentTaxBurden(this):
        federalTax = this.incomeBracket.getTax(this.taxable['federal'])
        stateTax = this.stateBracket.getTax(this.taxable['state'])
        capitalGainsTax = this.capitalGainsBracket.getTax(this.taxable['capitalgains'])
        return federalTax,stateTax,capitalGainsTax

    def investableFunds(this):
        return this.cash-this.annualSpending-this.currentTaxBurden()
 
    def getNetWorth(this):
        total = 0
        total = total+this.cash
        for account in this.accounts.values():
            total = total+account.balance
        
        return total

#---------------------------------------
#examples and tests

def testPaycheck():
    sim = career()
    sim.salary = 155000
    sim.federalW4 = w4()
    sim.federalW4.credits = 0
    sim.federalW4.deductions = 0
    #brackets here are just used for calculating withholding
    sim.brackets = taxBracket.getBracketsForYear(2021)
    sim.preTaxBenefits = {"dental":39.44,"medical":318.81,"vision":33.83}
    sim.postTaxBenefits = {"life":14}
    sim.preTaxInvestments = {accountType.HSA:300,accountType.TRADITIONAL401K:1625}
    return sim.getPaycheck(),sim.getCumulativePaycheck(12)